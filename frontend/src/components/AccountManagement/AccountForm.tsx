import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
  Box,
  FormControlLabel,
  Switch,
  MenuItem,
  Alert,
  Typography,
  Divider,
} from '@mui/material';
import { Account } from '../../types';
import { 
  PLATFORMS,
  ACCOUNT_DEFAULTS,
  type Platform
} from '../../config/accountConstants';

interface AccountFormProps {
  open: boolean;
  onClose: () => void;
  onSubmit: (accountData: Omit<Account, 'id' | 'created_at'> | Partial<Account>) => Promise<void>;
  account?: Account | null; // null for create, Account for edit
  loading?: boolean;
  title?: string;
}

interface AccountFormData {
  name: string;
  platform_username: string;
  user_id: number;
  account_type: Platform;
  data_processing_enabled: boolean;
  is_active: boolean;
}

/**
 * Account Form Component  
 * Follows Single Responsibility Principle - handles only account form operations
 * Open/Closed Principle - extensible for new account types and fields
 */
const AccountForm: React.FC<AccountFormProps> = ({
  open,
  onClose,
  onSubmit,
  account = null,
  loading = false,
  title,
}) => {
  const isEdit = !!account;
  const dialogTitle = title || (isEdit ? 'Edit Account' : 'Create New Account');

  const [formData, setFormData] = useState<AccountFormData>({
    name: '',
    platform_username: '',
    user_id: 1, // Default - should be set from current user context
    account_type: ACCOUNT_DEFAULTS.PLATFORM,
    data_processing_enabled: true,
    is_active: true,
  });

  const [errors, setErrors] = useState<Partial<AccountFormData>>({});
  const [submitError, setSubmitError] = useState<string>('');

  // Reset form when dialog opens/closes or account changes
  useEffect(() => {
    if (open) {
      if (account) {
        setFormData({
          name: account.name,
          platform_username: account.platform_username,
          user_id: account.user_id,
          account_type: account.account_type || ACCOUNT_DEFAULTS.PLATFORM,
          data_processing_enabled: account.data_processing_enabled ?? true,
          is_active: account.is_active,
        });
      } else {
        setFormData({
          name: '',
          platform_username: '',
          user_id: 1,
          account_type: ACCOUNT_DEFAULTS.PLATFORM,
          data_processing_enabled: true,
          is_active: true,
        });
      }
      setErrors({});
      setSubmitError('');
    }
  }, [open, account]);

  const validateForm = (): boolean => {
    const newErrors: Partial<AccountFormData> = {};

    if (!formData.name.trim()) {
      newErrors.name = 'Account name is required';
    }

    if (!formData.platform_username.trim()) {
      newErrors.platform_username = 'Platform username is required';
    } else if (formData.platform_username.length < 3) {
      newErrors.platform_username = 'Platform username must be at least 3 characters';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async () => {
    if (!validateForm()) return;

    try {
      setSubmitError('');
      
      const submitData = isEdit 
        ? { id: account!.id, ...formData }
        : formData;

      await onSubmit(submitData);
      onClose();
    } catch (error) {
      setSubmitError(error instanceof Error ? error.message : 'Failed to save account');
    }
  };

  const handleInputChange = (field: keyof AccountFormData) => (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    const value = event.target.type === 'checkbox' 
      ? event.target.checked 
      : event.target.value;
    
    setFormData(prev => ({ ...prev, [field]: value }));
    
    // Clear error for this field
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: undefined }));
    }
  };


  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="sm"
      fullWidth
      PaperProps={{
        sx: { minHeight: 400 }
      }}
    >
      <DialogTitle>
        <Typography variant="h6">{dialogTitle}</Typography>
      </DialogTitle>
      
      <DialogContent dividers>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 1 }}>
          {submitError && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {submitError}
            </Alert>
          )}

          {/* Basic Information */}
          <Typography variant="subtitle2" color="primary" gutterBottom>
            Basic Information
          </Typography>
          
          <TextField
            fullWidth
            label="Account Name"
            value={formData.name}
            onChange={handleInputChange('name')}
            error={!!errors.name}
            helperText={errors.name || 'A friendly name for this account'}
            required
          />

          <TextField
            fullWidth
            label="Platform Username"
            value={formData.platform_username}
            onChange={handleInputChange('platform_username')}
            error={!!errors.platform_username}
            helperText={errors.platform_username || 'The username for this platform account'}
            required
          />

          <TextField
            fullWidth
            select
            label="Account Type"
            value={formData.account_type}
            onChange={handleInputChange('account_type')}
          >
            <MenuItem value="ebay">eBay</MenuItem>
            <MenuItem value="ebay_motors">eBay Motors</MenuItem>
            <MenuItem value="ebay_store">eBay Store</MenuItem>
          </TextField>

          <Divider />

          {/* Data Processing Settings */}
          <Typography variant="subtitle2" color="primary" gutterBottom>
            Data Processing
          </Typography>

          <Box>
            <FormControlLabel
              control={
                <Switch
                  checked={formData.data_processing_enabled}
                  onChange={handleInputChange('data_processing_enabled')}
                />
              }
              label="Process CSV Files"
            />
            <Typography variant="body2" color="text.secondary" sx={{ ml: 4, mt: 0.5 }}>
              When enabled, uploaded CSV files will be automatically processed and imported into the system
            </Typography>
          </Box>

          <FormControlLabel
            control={
              <Switch
                checked={formData.is_active}
                onChange={handleInputChange('is_active')}
              />
            }
            label="Account Active"
          />
        </Box>
      </DialogContent>

      <DialogActions sx={{ p: 2, gap: 1 }}>
        <Button onClick={onClose} disabled={loading}>
          Cancel
        </Button>
        <Button
          onClick={handleSubmit}
          disabled={loading}
          variant="contained"
          color="primary"
        >
          {loading ? 'Loading...' : (isEdit ? 'Update Account' : 'Create Account')}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default AccountForm;