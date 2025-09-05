import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  Box,
  Alert,
  RadioGroup,
  FormControlLabel,
  Radio,
  FormControl,
  FormLabel,
  Divider,
  Chip,
  CircularProgress,
  Paper,
} from '@mui/material';
import {
  Warning as WarningIcon,
  Delete as DeleteIcon,
  Archive as ArchiveIcon,
  Info as InfoIcon,
} from '@mui/icons-material';

import { accountsAPI } from '../../services/api';
import { Account } from '../../types';

interface AccountDeletionDialogProps {
  open: boolean;
  account: Account | null;
  onClose: () => void;
  onConfirm: (action: 'transfer' | 'delete') => Promise<void>;
  loading?: boolean;
}

interface DeletionImpact {
  account_id: number;
  account_name: string;
  is_active: boolean;
  can_delete: boolean;
  reason?: string;
  data_impact?: {
    orders: number;
    listings: number;
    permissions: number;
    settings: number;
    total_records: number;
  };
  is_guest_account: boolean;
}

/**
 * Enhanced Account Deletion Dialog
 * 
 * Provides options for data preservation when deleting accounts:
 * - Transfer data to GUEST account (preserve data)
 * - Permanently delete account and all data
 * 
 * Follows SOLID principles with clear separation of concerns
 */
const AccountDeletionDialog: React.FC<AccountDeletionDialogProps> = ({
  open,
  account,
  onClose,
  onConfirm,
  loading = false,
}) => {
  const [selectedAction, setSelectedAction] = useState<'transfer' | 'delete'>('transfer');
  const [deletionImpact, setDeletionImpact] = useState<DeletionImpact | null>(null);
  const [loadingImpact, setLoadingImpact] = useState(false);
  const [impactError, setImpactError] = useState<string | null>(null);

  // Load deletion impact when dialog opens
  useEffect(() => {
    if (open && account) {
      loadDeletionImpact();
    }
  }, [open, account]);

  const loadDeletionImpact = async () => {
    if (!account) return;

    setLoadingImpact(true);
    setImpactError(null);
    
    try {
      const impact = await accountsAPI.getDeletionImpact(account.id);
      setDeletionImpact(impact);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to load deletion impact';
      setImpactError(errorMessage);
    } finally {
      setLoadingImpact(false);
    }
  };

  const handleClose = () => {
    setSelectedAction('transfer');
    setDeletionImpact(null);
    setImpactError(null);
    onClose();
  };

  const handleConfirm = async () => {
    await onConfirm(selectedAction);
    handleClose();
  };

  const renderDataImpactSummary = () => {
    if (!deletionImpact?.data_impact) return null;

    const { data_impact } = deletionImpact;
    const hasData = data_impact.total_records > 0;

    return (
      <Paper sx={{ p: 2, mt: 2, backgroundColor: 'background.default' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
          <InfoIcon color="info" sx={{ mr: 1 }} />
          <Typography variant="subtitle2" fontWeight="bold">
            Data Impact Summary
          </Typography>
        </Box>
        
        {hasData ? (
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
            <Chip 
              label={`${data_impact.orders} Orders`} 
              size="small" 
              color={data_impact.orders > 0 ? "primary" : "default"}
            />
            <Chip 
              label={`${data_impact.listings} Listings`} 
              size="small" 
              color={data_impact.listings > 0 ? "secondary" : "default"}
            />
            <Chip 
              label={`${data_impact.permissions} Permissions`} 
              size="small" 
              variant="outlined"
            />
            <Chip 
              label={`${data_impact.settings} Settings`} 
              size="small" 
              variant="outlined"
            />
          </Box>
        ) : (
          <Typography variant="body2" color="text.secondary">
            No data will be affected
          </Typography>
        )}
      </Paper>
    );
  };

  const renderActionOptions = () => {
    if (!deletionImpact) return null;

    const { is_active, data_impact } = deletionImpact;
    const hasData = data_impact && data_impact.total_records > 0;

    if (is_active) {
      return (
        <Alert severity="info" sx={{ mt: 2 }}>
          <Typography variant="body2">
            This account is currently active and will be <strong>deactivated</strong> first. 
            You can then choose the final data handling option.
          </Typography>
        </Alert>
      );
    }

    if (!hasData) {
      return (
        <Alert severity="info" sx={{ mt: 2 }}>
          <Typography variant="body2">
            This account has no associated data and will be permanently deleted.
          </Typography>
        </Alert>
      );
    }

    return (
      <FormControl component="fieldset" sx={{ mt: 2, width: '100%' }}>
        <FormLabel component="legend">Choose data handling option:</FormLabel>
        <RadioGroup
          value={selectedAction}
          onChange={(e) => setSelectedAction(e.target.value as 'transfer' | 'delete')}
          sx={{ mt: 1 }}
        >
          <FormControlLabel
            value="transfer"
            control={<Radio />}
            label={
              <Box sx={{ ml: 1 }}>
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <ArchiveIcon sx={{ mr: 1, color: 'primary.main' }} />
                  <Typography variant="body1" fontWeight="medium">
                    Transfer data to GUEST account
                  </Typography>
                </Box>
                <Typography variant="body2" color="text.secondary" sx={{ ml: 3 }}>
                  Preserve all orders and listings in a system GUEST account for historical reference
                </Typography>
              </Box>
            }
          />
          
          <FormControlLabel
            value="delete"
            control={<Radio />}
            label={
              <Box sx={{ ml: 1 }}>
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <DeleteIcon sx={{ mr: 1, color: 'error.main' }} />
                  <Typography variant="body1" fontWeight="medium" color="error.main">
                    Permanently delete all data
                  </Typography>
                </Box>
                <Typography variant="body2" color="text.secondary" sx={{ ml: 3 }}>
                  Completely remove account and all associated orders, listings, and settings
                </Typography>
              </Box>
            }
          />
        </RadioGroup>
      </FormControl>
    );
  };

  const getDialogTitle = () => {
    if (!deletionImpact) return "Delete Account";
    
    if (deletionImpact.is_active) {
      return "Deactivate Account";
    }
    
    return selectedAction === 'transfer' ? "Transfer Account Data" : "Delete Account Permanently";
  };

  const getConfirmButtonText = () => {
    if (loading) return "Processing...";
    if (!deletionImpact) return "Delete";
    
    if (deletionImpact.is_active) {
      return "Deactivate Account";
    }
    
    return selectedAction === 'transfer' ? "Transfer to GUEST" : "Delete Permanently";
  };

  const getConfirmButtonColor = () => {
    if (!deletionImpact || deletionImpact.is_active) return "warning";
    return selectedAction === 'transfer' ? "primary" : "error";
  };

  if (!account) return null;

  return (
    <Dialog
      open={open}
      onClose={handleClose}
      maxWidth="md"
      fullWidth
      PaperProps={{
        sx: { minHeight: 400 }
      }}
    >
      <DialogTitle sx={{ display: 'flex', alignItems: 'center' }}>
        <WarningIcon color="warning" sx={{ mr: 1 }} />
        {getDialogTitle()}
      </DialogTitle>
      
      <DialogContent>
        {loadingImpact ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
            <CircularProgress />
          </Box>
        ) : impactError ? (
          <Alert severity="error" sx={{ mb: 2 }}>
            <Typography variant="body2">
              Error loading account information: {impactError}
            </Typography>
          </Alert>
        ) : deletionImpact ? (
          <>
            <Typography variant="body1" sx={{ mb: 2 }}>
              You are about to {deletionImpact.is_active ? 'deactivate' : 'delete'} the account:{' '}
              <strong>{deletionImpact.account_name}</strong>
            </Typography>

            {deletionImpact.is_guest_account && (
              <Alert severity="error" sx={{ mb: 2 }}>
                <Typography variant="body2">
                  This is the system GUEST account and cannot be deleted.
                </Typography>
              </Alert>
            )}

            {!deletionImpact.can_delete && (
              <Alert severity="error" sx={{ mb: 2 }}>
                <Typography variant="body2">
                  {deletionImpact.reason}
                </Typography>
              </Alert>
            )}

            {renderDataImpactSummary()}
            {deletionImpact.can_delete && renderActionOptions()}

            {selectedAction === 'delete' && !deletionImpact.is_active && (
              <Alert severity="warning" sx={{ mt: 2 }}>
                <Typography variant="body2" fontWeight="medium">
                  ⚠️ This action cannot be undone! All data will be permanently lost.
                </Typography>
              </Alert>
            )}
          </>
        ) : null}
      </DialogContent>

      <Divider />

      <DialogActions sx={{ p: 2, justifyContent: 'space-between' }}>
        <Button onClick={handleClose} disabled={loading}>
          Cancel
        </Button>
        
        <Button
          onClick={handleConfirm}
          variant="contained"
          color={getConfirmButtonColor()}
          disabled={loading || !deletionImpact?.can_delete}
          startIcon={loading ? <CircularProgress size={20} /> : undefined}
        >
          {getConfirmButtonText()}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default AccountDeletionDialog;