import React, { useState } from 'react';
import {
  FormControl,
  Select,
  MenuItem,
  Chip,
  CircularProgress,
  Box,
  SelectChangeEvent,
} from '@mui/material';

interface ListingStatusToggleProps {
  currentStatus: string;
  onStatusChange: (newStatus: string) => Promise<void>;
  disabled?: boolean;
}

const ListingStatusToggle: React.FC<ListingStatusToggleProps> = ({
  currentStatus,
  onStatusChange,
  disabled = false,
}) => {
  const [status, setStatus] = useState(currentStatus.toLowerCase());
  const [isUpdating, setIsUpdating] = useState(false);

  const statusOptions = [
    { value: 'active', label: 'Active', color: 'success' as const },
    { value: 'inactive', label: 'Inactive', color: 'default' as const },
    { value: 'ended', label: 'Ended', color: 'warning' as const },
    { value: 'sold', label: 'Sold', color: 'info' as const },
  ];

  const getCurrentStatusOption = () => {
    return statusOptions.find(option => option.value === status) || statusOptions[0];
  };

  const handleStatusChange = async (event: SelectChangeEvent) => {
    const newStatus = event.target.value;
    if (newStatus === status || isUpdating) return;

    setIsUpdating(true);
    try {
      await onStatusChange(newStatus);
      setStatus(newStatus);
    } catch (error) {
      console.error('Failed to update status:', error);
      // Keep old status on error
    } finally {
      setIsUpdating(false);
    }
  };

  const currentOption = getCurrentStatusOption();

  if (disabled) {
    return (
      <Chip
        label={currentOption.label}
        color={currentOption.color}
        size="small"
        variant="outlined"
      />
    );
  }

  return (
    <Box sx={{ minWidth: 100, position: 'relative' }}>
      <FormControl size="small" fullWidth disabled={isUpdating}>
        <Select
          value={status}
          onChange={handleStatusChange}
          displayEmpty
          variant="outlined"
          sx={{
            '& .MuiOutlinedInput-notchedOutline': {
              border: 'none',
            },
            '& .MuiSelect-select': {
              padding: '2px 8px',
              fontSize: '0.75rem',
            },
            minHeight: 'auto',
          }}
          renderValue={(value) => {
            const option = statusOptions.find(opt => opt.value === value);
            if (!option) return '';
            
            return (
              <Chip
                label={option.label}
                color={option.color}
                size="small"
                variant="filled"
                sx={{ 
                  minWidth: 'auto',
                  height: '20px',
                  '& .MuiChip-label': {
                    fontSize: '0.65rem',
                    px: 1,
                  }
                }}
              />
            );
          }}
        >
          {statusOptions.map((option) => (
            <MenuItem key={option.value} value={option.value}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Chip
                  label={option.label}
                  color={option.color}
                  size="small"
                  variant="outlined"
                />
              </Box>
            </MenuItem>
          ))}
        </Select>
      </FormControl>
      
      {isUpdating && (
        <Box
          sx={{
            position: 'absolute',
            top: '50%',
            right: 8,
            transform: 'translateY(-50%)',
            display: 'flex',
            alignItems: 'center',
          }}
        >
          <CircularProgress size={12} />
        </Box>
      )}
    </Box>
  );
};

export default ListingStatusToggle;