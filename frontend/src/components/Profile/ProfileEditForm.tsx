import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
  Box,
  Typography,
  Alert,
  Grid,
  IconButton,
} from '@mui/material';
import {
  Close as CloseIcon,
  Save as SaveIcon,
} from '@mui/icons-material';
import { ProfileData, ProfileUpdate } from '../../services/profileAPI';

interface ProfileEditFormProps {
  open: boolean;
  onClose: () => void;
  onSave: (data: ProfileUpdate) => Promise<void>;
  profile: ProfileData;
  isLoading?: boolean;
}

const ProfileEditForm: React.FC<ProfileEditFormProps> = ({
  open,
  onClose,
  onSave,
  profile,
  isLoading = false,
}) => {
  const [formData, setFormData] = useState<ProfileUpdate>({
    bio: '',
    phone: '',
  });
  const [errors, setErrors] = useState<Partial<ProfileUpdate>>({});
  const [submitError, setSubmitError] = useState<string>('');

  // Initialize form data when profile changes
  useEffect(() => {
    if (profile) {
      setFormData({
        bio: profile.bio || '',
        phone: profile.phone || '',
      });
    }
  }, [profile]);

  // Reset form when dialog opens/closes
  useEffect(() => {
    if (!open) {
      setErrors({});
      setSubmitError('');
    }
  }, [open]);

  const validateForm = (): boolean => {
    const newErrors: Partial<ProfileUpdate> = {};

    // Phone validation
    if (formData.phone && formData.phone.trim()) {
      const phoneRegex = /^[\+]?[1-9][\d]{0,15}$/;
      if (!phoneRegex.test(formData.phone.replace(/[\s\-\(\)]/g, ''))) {
        newErrors.phone = 'Please enter a valid phone number';
      }
    }

    // Bio validation
    if (formData.bio && formData.bio.length > 500) {
      newErrors.bio = 'Bio must be 500 characters or less';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleInputChange = (field: keyof ProfileUpdate) => (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    const value = event.target.value;
    setFormData(prev => ({ ...prev, [field]: value }));
    
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: undefined }));
    }
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setSubmitError('');

    if (!validateForm()) {
      return;
    }

    try {
      // Only send fields that have changed
      const changedData: ProfileUpdate = {};
      if (formData.bio !== (profile.bio || '')) {
        changedData.bio = formData.bio;
      }
      if (formData.phone !== (profile.phone || '')) {
        changedData.phone = formData.phone;
      }

      // If no changes were made, just close the dialog
      if (Object.keys(changedData).length === 0) {
        onClose();
        return;
      }

      await onSave(changedData);
      onClose();
    } catch (error) {
      setSubmitError(
        error instanceof Error ? error.message : 'Failed to update profile'
      );
    }
  };

  const handleCancel = () => {
    // Reset form data to original values
    setFormData({
      bio: profile.bio || '',
      phone: profile.phone || '',
    });
    onClose();
  };

  const hasChanges = () => {
    return (
      formData.bio !== (profile.bio || '') ||
      formData.phone !== (profile.phone || '')
    );
  };

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="sm"
      fullWidth
      PaperProps={{
        sx: { borderRadius: 2 }
      }}
    >
      <DialogTitle sx={{ pb: 1 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="h6" component="div" sx={{ fontWeight: 600 }}>
            Edit Profile
          </Typography>
          <IconButton
            onClick={onClose}
            size="small"
            sx={{ color: 'grey.500' }}
          >
            <CloseIcon />
          </IconButton>
        </Box>
        <Typography variant="body2" sx={{ color: 'text.secondary', mt: 1 }}>
          Update your profile information
        </Typography>
      </DialogTitle>

      <form onSubmit={handleSubmit}>
        <DialogContent sx={{ pt: 2 }}>
          {submitError && (
            <Alert severity="error" sx={{ mb: 3 }}>
              {submitError}
            </Alert>
          )}

          <Grid container spacing={3}>
            {/* Read-only fields for context */}
            <Grid item xs={12} sm={6}>
              <TextField
                label="Username"
                value={profile.username}
                disabled
                fullWidth
                variant="outlined"
                helperText="Username cannot be changed"
              />
            </Grid>

            <Grid item xs={12} sm={6}>
              <TextField
                label="Email"
                value={profile.email}
                disabled
                fullWidth
                variant="outlined"
                helperText="Contact admin to change email"
              />
            </Grid>

            {/* Editable fields */}
            <Grid item xs={12}>
              <TextField
                label="Phone Number"
                value={formData.phone}
                onChange={handleInputChange('phone')}
                error={!!errors.phone}
                helperText={errors.phone || 'Optional - Your contact phone number'}
                fullWidth
                variant="outlined"
                placeholder="+1 (555) 123-4567"
                disabled={isLoading}
              />
            </Grid>

            <Grid item xs={12}>
              <TextField
                label="Bio"
                value={formData.bio}
                onChange={handleInputChange('bio')}
                error={!!errors.bio}
                helperText={
                  errors.bio || 
                  `Tell us about yourself (${formData.bio.length}/500 characters)`
                }
                fullWidth
                multiline
                rows={4}
                variant="outlined"
                placeholder="Write a brief description about yourself, your role, or interests..."
                disabled={isLoading}
                inputProps={{ maxLength: 500 }}
              />
            </Grid>

            {/* Role and Status Display */}
            <Grid item xs={12} sm={6}>
              <TextField
                label="Role"
                value={profile.role.charAt(0).toUpperCase() + profile.role.slice(1)}
                disabled
                fullWidth
                variant="outlined"
                helperText="Role is managed by administrators"
              />
            </Grid>

            <Grid item xs={12} sm={6}>
              <TextField
                label="Account Status"
                value={profile.is_active ? 'Active' : 'Inactive'}
                disabled
                fullWidth
                variant="outlined"
                helperText="Status is managed by administrators"
              />
            </Grid>
          </Grid>
        </DialogContent>

        <DialogActions sx={{ px: 3, py: 2 }}>
          <Button
            onClick={handleCancel}
            disabled={isLoading}
            sx={{ minWidth: 80 }}
          >
            Cancel
          </Button>
          <Button
            type="submit"
            variant="contained"
            disabled={isLoading || !hasChanges()}
            startIcon={<SaveIcon />}
            sx={{ minWidth: 120 }}
          >
            {isLoading ? 'Saving...' : 'Save Changes'}
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  );
};

export default ProfileEditForm;