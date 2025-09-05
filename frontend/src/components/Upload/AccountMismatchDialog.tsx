import React from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  Alert,
  Box,
  Chip,
} from '@mui/material';
import { Warning, AccountCircle } from '@mui/icons-material';

interface AccountMismatchDialogProps {
  open: boolean;
  onClose: () => void;
  onConfirm: () => void;
  fileName: string;
  detectedUsername: string;
  selectedAccountName: string;
  selectedAccountUsername?: string;
}

const AccountMismatchDialog: React.FC<AccountMismatchDialogProps> = ({
  open,
  onClose,
  onConfirm,
  fileName,
  detectedUsername,
  selectedAccountName,
  selectedAccountUsername,
}) => {
  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="sm"
      fullWidth
    >
      <DialogTitle sx={{ display: 'flex', alignItems: 'center', gap: 1, color: 'warning.main' }}>
        <Warning />
        Account Mismatch Warning
      </DialogTitle>
      
      <DialogContent>
        <Alert severity="warning" sx={{ mb: 2 }}>
          The detected username from the CSV file doesn't match the selected account. 
          This may cause data integrity issues.
        </Alert>
        
        <Box sx={{ mb: 2 }}>
          <Typography variant="subtitle2" color="text.secondary" gutterBottom>
            File:
          </Typography>
          <Typography variant="body1" sx={{ fontWeight: 'medium' }}>
            {fileName}
          </Typography>
        </Box>
        
        <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
          <Box sx={{ flex: 1 }}>
            <Typography variant="subtitle2" color="text.secondary" gutterBottom>
              Detected User:
            </Typography>
            <Chip
              icon={<AccountCircle />}
              label={detectedUsername}
              color="primary"
              variant="outlined"
              size="small"
            />
          </Box>
          
          <Box sx={{ flex: 1 }}>
            <Typography variant="subtitle2" color="text.secondary" gutterBottom>
              Selected Account:
            </Typography>
            <Chip
              icon={<AccountCircle />}
              label={`${selectedAccountName}${selectedAccountUsername ? ` (${selectedAccountUsername})` : ''}`}
              color="warning"
              variant="outlined"
              size="small"
            />
          </Box>
        </Box>
        
        <Typography variant="body2" color="text.secondary">
          <strong>Risks:</strong>
        </Typography>
        <ul style={{ margin: '8px 0', paddingLeft: '20px' }}>
          <li>
            <Typography variant="body2" color="text.secondary">
              Orders/Listings will be associated with wrong account
            </Typography>
          </li>
          <li>
            <Typography variant="body2" color="text.secondary">
              Reports and analytics will show incorrect data
            </Typography>
          </li>
          <li>
            <Typography variant="body2" color="text.secondary">
              Difficult to fix data once uploaded to wrong account
            </Typography>
          </li>
        </ul>
        
        <Alert severity="info" sx={{ mt: 2 }}>
          <Typography variant="body2">
            <strong>Recommendation:</strong> Select the correct account that matches username "{detectedUsername}" 
            before uploading.
          </Typography>
        </Alert>
      </DialogContent>
      
      <DialogActions>
        <Button onClick={onClose} variant="contained" color="primary">
          Cancel & Fix
        </Button>
        <Button onClick={onConfirm} variant="outlined" color="warning">
          Upload Anyway
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default AccountMismatchDialog;