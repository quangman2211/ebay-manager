import React, { useState, useEffect } from 'react';
import {
  TextField,
  IconButton,
  Box,
  Typography,
  CircularProgress,
  InputAdornment,
} from '@mui/material';
import { Check as CheckIcon, Close as CancelIcon, Edit as EditIcon } from '@mui/icons-material';

interface InlineEditableFieldProps {
  value: string | number;
  onSave: (value: string) => Promise<void>;
  type?: 'text' | 'number' | 'price';
  label?: string;
  disabled?: boolean;
  placeholder?: string;
  validation?: (value: string) => string | null; // Returns error message or null
}

const InlineEditableField: React.FC<InlineEditableFieldProps> = ({
  value,
  onSave,
  type = 'text',
  label,
  disabled = false,
  placeholder,
  validation,
}) => {
  const [isEditing, setIsEditing] = useState(false);
  const [editValue, setEditValue] = useState(String(value));
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setEditValue(String(value));
  }, [value]);

  const handleStartEdit = () => {
    if (disabled) return;
    setIsEditing(true);
    setEditValue(String(value));
    setError(null);
  };

  const handleCancel = () => {
    setIsEditing(false);
    setEditValue(String(value));
    setError(null);
  };

  const handleSave = async () => {
    if (validation) {
      const validationError = validation(editValue);
      if (validationError) {
        setError(validationError);
        return;
      }
    }

    setIsLoading(true);
    setError(null);

    try {
      await onSave(editValue);
      setIsEditing(false);
    } catch (error: any) {
      setError(error.response?.data?.detail || 'Failed to save');
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter') {
      handleSave();
    } else if (event.key === 'Escape') {
      handleCancel();
    }
  };

  const formatDisplayValue = (val: string | number): string => {
    if (type === 'price') {
      const numVal = parseFloat(String(val));
      return isNaN(numVal) ? String(val) : `$${numVal.toFixed(2)}`;
    }
    return String(val);
  };

  const getInputProps = () => {
    const baseProps: any = {
      size: 'small',
      value: editValue,
      onChange: (e: React.ChangeEvent<HTMLInputElement>) => setEditValue(e.target.value),
      onKeyDown: handleKeyPress,
      error: !!error,
      helperText: error,
      disabled: isLoading,
      autoFocus: true,
      placeholder,
    };

    if (type === 'number') {
      baseProps.type = 'number';
      baseProps.inputProps = { min: 0 };
    } else if (type === 'price') {
      baseProps.InputProps = {
        startAdornment: <InputAdornment position="start">$</InputAdornment>,
      };
    }

    return baseProps;
  };

  if (isEditing) {
    return (
      <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1 }}>
        <TextField
          {...getInputProps()}
          sx={{ 
            minWidth: 120,
            '& .MuiOutlinedInput-root': {
              fontSize: '0.875rem',
            }
          }}
        />
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, pt: 0.5 }}>
          <IconButton
            size="small"
            onClick={handleSave}
            disabled={isLoading}
            color="primary"
          >
            {isLoading ? <CircularProgress size={16} /> : <CheckIcon fontSize="small" />}
          </IconButton>
          <IconButton
            size="small"
            onClick={handleCancel}
            disabled={isLoading}
          >
            <CancelIcon fontSize="small" />
          </IconButton>
        </Box>
      </Box>
    );
  }

  return (
    <Box 
      sx={{ 
        display: 'flex', 
        alignItems: 'center', 
        gap: 1,
        cursor: disabled ? 'default' : 'pointer',
        '&:hover .edit-icon': {
          opacity: disabled ? 0 : 1,
        }
      }}
      onClick={handleStartEdit}
    >
      <Typography 
        variant="body2" 
        sx={{ 
          minHeight: '20px',
          color: disabled ? 'text.disabled' : 'text.primary'
        }}
      >
        {formatDisplayValue(value)}
      </Typography>
      {!disabled && (
        <EditIcon 
          className="edit-icon"
          fontSize="small" 
          sx={{ 
            opacity: 0,
            transition: 'opacity 0.2s',
            color: 'action.active',
            fontSize: '16px'
          }} 
        />
      )}
    </Box>
  );
};

export default InlineEditableField;