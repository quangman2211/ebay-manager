import React, { useState } from 'react';
import {
  Box,
  TextField,
  IconButton,
  Typography,
  CircularProgress,
  Snackbar,
  Alert,
  Chip,
} from '@mui/material';
import { Edit, Save, Cancel, LocalShipping } from '@mui/icons-material';
import OrderDataService from '../../services/OrderDataService';
import { colors } from '../../styles/common/colors';
import { spacing } from '../../styles/common/spacing';
import type { Order } from '../../types';

interface TrackingNumberInputProps {
  order: Order;
  onTrackingUpdate: (orderId: number, trackingNumber: string) => void;
}

interface ITrackingValidator {
  isValidTrackingNumber(trackingNumber: string): boolean;
  getTrackingErrors(trackingNumber: string): string[];
}

class TrackingValidator implements ITrackingValidator {
  private trackingPatterns = [
    /^1Z[0-9A-Z]{16}$/,           // UPS
    /^[0-9]{12}$/,                // FedEx 12 digits
    /^[0-9]{14}$/,                // FedEx 14 digits
    /^[0-9]{20}$/,                // FedEx 20 digits
    /^[0-9]{22}$/,                // USPS 22 digits
    /^[A-Z]{2}[0-9]{9}US$/,       // USPS International
    /^420[0-9]{5}[0-9]{22}$/,     // USPS Priority
    /^[0-9]{13}$/,                // DHL 13 digits
    /^[A-Z0-9]{10}$/,             // DHL 10 alphanumeric
  ];

  isValidTrackingNumber(trackingNumber: string): boolean {
    if (!trackingNumber || trackingNumber.length < 8) return false;
    return this.trackingPatterns.some(pattern => pattern.test(trackingNumber));
  }

  getTrackingErrors(trackingNumber: string): string[] {
    const errors: string[] = [];
    
    if (!trackingNumber) {
      errors.push('Tracking number is required');
    } else if (trackingNumber.length < 8) {
      errors.push('Tracking number must be at least 8 characters');
    } else if (!this.isValidTrackingNumber(trackingNumber)) {
      errors.push('Invalid tracking number format');
    }
    
    return errors;
  }
}

const trackingValidator = new TrackingValidator();

const TrackingNumberInput: React.FC<TrackingNumberInputProps> = ({ order, onTrackingUpdate }) => {
  const currentTracking = order.csv_row['Tracking Number'] || '';
  const [isEditing, setIsEditing] = useState(false);
  const [trackingNumber, setTrackingNumber] = useState(currentTracking);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleEditClick = () => {
    setIsEditing(true);
    setTrackingNumber(currentTracking);
  };

  const handleCancelEdit = () => {
    setIsEditing(false);
    setTrackingNumber(currentTracking);
    setError(null);
  };

  const handleSaveTracking = async () => {
    const trimmedTracking = trackingNumber.trim();
    
    if (trimmedTracking === currentTracking) {
      setIsEditing(false);
      return;
    }

    if (trimmedTracking && !trackingValidator.isValidTrackingNumber(trimmedTracking)) {
      const errors = trackingValidator.getTrackingErrors(trimmedTracking);
      setError(errors.join(', '));
      return;
    }

    setLoading(true);
    try {
      await OrderDataService.updateTrackingNumber(order.id, trimmedTracking);
      onTrackingUpdate(order.id, trimmedTracking);
      setIsEditing(false);
      setError(null);
    } catch (error) {
      console.error('Failed to update tracking number:', error);
      setError('Failed to update tracking number. Please try again.');
      setTrackingNumber(currentTracking);
    } finally {
      setLoading(false);
    }
  };

  if (isEditing) {
    return (
      <Box sx={{ display: 'flex', alignItems: 'center', gap: spacing.small, width: '100%' }}>
        <TextField
          value={trackingNumber}
          onChange={(e) => setTrackingNumber(e.target.value)}
          size="small"
          placeholder="Enter tracking number"
          error={!!error}
          helperText={error}
          disabled={loading}
          sx={{ flexGrow: 1, minWidth: 150 }}
        />
        
        <IconButton 
          size="small" 
          onClick={handleSaveTracking}
          disabled={loading}
          sx={{ color: colors.success }}
        >
          {loading ? <CircularProgress size={16} /> : <Save />}
        </IconButton>
        
        <IconButton 
          size="small" 
          onClick={handleCancelEdit}
          disabled={loading}
          sx={{ color: colors.error }}
        >
          <Cancel />
        </IconButton>

        <Snackbar 
          open={!!error} 
          autoHideDuration={6000} 
          onClose={() => setError(null)}
        >
          <Alert severity="error" onClose={() => setError(null)}>
            {error}
          </Alert>
        </Snackbar>
      </Box>
    );
  }

  return (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: spacing.small }}>
      {currentTracking ? (
        <Chip
          icon={<LocalShipping />}
          label={currentTracking}
          variant="outlined"
          sx={{
            maxWidth: 150,
            '& .MuiChip-label': {
              fontSize: '0.75rem',
            },
          }}
        />
      ) : (
        <Typography variant="body2" sx={{ color: colors.text.secondary, fontSize: '0.75rem' }}>
          No tracking
        </Typography>
      )}
      
      <IconButton 
        size="small" 
        onClick={handleEditClick}
        sx={{ color: colors.text.secondary }}
      >
        <Edit />
      </IconButton>
    </Box>
  );
};

export default TrackingNumberInput;