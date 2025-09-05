import React, { useState } from 'react';
import {
  Box,
  Typography,
  Alert,
  Button,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Collapse,
  IconButton,
} from '@mui/material';
import {
  Error,
  Refresh,
  LightbulbOutlined,
  ExpandMore,
  ExpandLess,
  HelpOutline,
  ContactSupport,
} from '@mui/icons-material';

interface ErrorRecoveryPanelProps {
  error: {
    code: string;
    message: string;
    suggestions: string[];
  };
  filename?: string;
  onRetry: () => void;
  onCancel: () => void;
  retrying?: boolean;
  retryCount?: number;
  maxRetries?: number;
}

const ErrorRecoveryPanel: React.FC<ErrorRecoveryPanelProps> = ({
  error,
  filename,
  onRetry,
  onCancel,
  retrying = false,
  retryCount = 0,
  maxRetries = 3,
}) => {
  const [showDetails, setShowDetails] = useState(false);
  const [showTroubleshooting, setShowTroubleshooting] = useState(false);

  const getErrorSeverity = () => {
    switch (error.code) {
      case 'FILE_TOO_LARGE':
      case 'INVALID_CSV_FORMAT':
      case 'MISSING_COLUMNS':
        return 'warning';
      case 'PERMISSION_DENIED':
        return 'error';
      default:
        return 'error';
    }
  };

  const getRetryButtonText = () => {
    if (retrying) return 'Retrying...';
    if (retryCount > 0) return `Retry (${maxRetries - retryCount} left)`;
    return 'Retry Upload';
  };

  const getTroubleshootingTips = () => {
    const tips: { [key: string]: string[] } = {
      'FILE_TOO_LARGE': [
        'Split your CSV file into smaller chunks (under 50MB each)',
        'Remove unnecessary columns or data to reduce file size',
        'Use a CSV editor to compress the file',
        'Contact support if you need to increase the file size limit',
      ],
      'INVALID_CSV_FORMAT': [
        'Ensure the file is saved as UTF-8 encoded CSV',
        'Check that columns are properly separated by commas',
        'Remove any special characters or formatting from the file',
        'Try exporting the data again from eBay Seller Hub',
      ],
      'MISSING_COLUMNS': [
        'Verify your CSV has all required column headers',
        'Check the spelling of column names exactly matches eBay format',
        'Ensure no empty columns exist in your CSV file',
        'Download a fresh CSV export from eBay Seller Hub',
      ],
      'PERMISSION_DENIED': [
        'Contact your administrator to request access to this account',
        'Check if your account permissions have been recently changed',
        'Try logging out and logging back in',
        'Verify you are selecting the correct account',
      ],
    };

    return tips[error.code] || [
      'Check your internet connection and try again',
      'Ensure the file is not corrupted',
      'Try uploading during off-peak hours',
      'Contact support if the problem persists',
    ];
  };

  return (
    <Card sx={{ border: '2px solid', borderColor: 'error.main', mb: 2 }}>
      <CardContent>
        {/* Error Header */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
          <Error color="error" />
          <Typography variant="h6" color="error.main">
            Upload Failed
          </Typography>
          <Chip
            label={error.code}
            color="error"
            size="small"
            variant="outlined"
          />
        </Box>

        {/* File Info */}
        {filename && (
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            File: <strong>{filename}</strong>
          </Typography>
        )}

        {/* Error Message */}
        <Alert 
          severity={getErrorSeverity() as 'warning' | 'error'} 
          sx={{ mb: 2 }}
          action={
            <IconButton
              size="small"
              onClick={() => setShowDetails(!showDetails)}
              aria-label="show details"
            >
              {showDetails ? <ExpandLess /> : <ExpandMore />}
            </IconButton>
          }
        >
          <Typography variant="body2">
            {error.message}
          </Typography>
        </Alert>

        {/* Error Details */}
        <Collapse in={showDetails}>
          <Box sx={{ mb: 2 }}>
            <Typography variant="subtitle2" sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
              <HelpOutline fontSize="small" />
              Error Details
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ fontFamily: 'monospace', p: 1, bgcolor: 'grey.100', borderRadius: 1 }}>
              Code: {error.code}<br />
              Retry Count: {retryCount}/{maxRetries}
            </Typography>
          </Box>
        </Collapse>

        {/* Quick Suggestions */}
        {error.suggestions.length > 0 && (
          <Box sx={{ mb: 2 }}>
            <Typography variant="subtitle2" sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
              <LightbulbOutlined fontSize="small" color="warning" />
              Quick Fixes
            </Typography>
            <List dense>
              {error.suggestions.map((suggestion, index) => (
                <ListItem key={index} sx={{ py: 0.5 }}>
                  <ListItemIcon sx={{ minWidth: 32 }}>
                    <Typography variant="body2" color="primary">
                      {index + 1}.
                    </Typography>
                  </ListItemIcon>
                  <ListItemText
                    primary={
                      <Typography variant="body2">
                        {suggestion}
                      </Typography>
                    }
                  />
                </ListItem>
              ))}
            </List>
          </Box>
        )}

        {/* Action Buttons */}
        <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
          <Button
            variant="contained"
            color="primary"
            onClick={onRetry}
            disabled={retrying || retryCount >= maxRetries}
            startIcon={retrying ? <CircularProgress size={16} /> : <Refresh />}
          >
            {getRetryButtonText()}
          </Button>
          
          <Button
            variant="outlined"
            color="secondary"
            onClick={onCancel}
            disabled={retrying}
          >
            Cancel
          </Button>

          <Button
            variant="text"
            size="small"
            onClick={() => setShowTroubleshooting(!showTroubleshooting)}
            startIcon={<ContactSupport />}
          >
            Troubleshooting
          </Button>
        </Box>

        {/* Detailed Troubleshooting */}
        <Collapse in={showTroubleshooting}>
          <Box sx={{ mt: 2, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
            <Typography variant="subtitle2" sx={{ mb: 2 }}>
              🔧 Detailed Troubleshooting Steps
            </Typography>
            <List dense>
              {getTroubleshootingTips().map((tip, index) => (
                <ListItem key={index} sx={{ py: 0.5 }}>
                  <ListItemIcon sx={{ minWidth: 32 }}>
                    <Typography variant="body2" color="primary" sx={{ fontWeight: 'bold' }}>
                      {index + 1}.
                    </Typography>
                  </ListItemIcon>
                  <ListItemText
                    primary={
                      <Typography variant="body2">
                        {tip}
                      </Typography>
                    }
                  />
                </ListItem>
              ))}
            </List>
          </Box>
        </Collapse>

        {/* Retry Limit Warning */}
        {retryCount >= maxRetries && (
          <Alert severity="warning" sx={{ mt: 2 }}>
            <Typography variant="body2">
              Maximum retry attempts reached. Please check the troubleshooting steps above or contact support.
            </Typography>
          </Alert>
        )}
      </CardContent>
    </Card>
  );
};

export default ErrorRecoveryPanel;