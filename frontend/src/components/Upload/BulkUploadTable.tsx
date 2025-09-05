import React, { useState, useCallback } from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  FormControl,
  Select,
  MenuItem,
  Button,
  Chip,
  Typography,
  Box,
  LinearProgress,
  IconButton,
  Alert,
  Tooltip
} from '@mui/material';
import {
  Delete as DeleteIcon,
  Upload as UploadIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Refresh as RefreshIcon,
  Warning as WarningIcon,
  VerifiedUser as VerifiedUserIcon
} from '@mui/icons-material';
import type { Account } from '../../types';
import { DATA_TYPE_OPTIONS, DataType, DEFAULT_DATA_TYPE } from '../../constants/dataTypes';
import AccountMismatchDialog from './AccountMismatchDialog';

export interface BulkUploadFile {
  id: string;
  file: File;
  selectedAccountId?: number;
  dataType: DataType;
  status: 'pending' | 'uploading' | 'completed' | 'failed';
  progress: number;
  message?: string;
  detectedUsername?: string;
  suggestedAccounts: Array<{
    id: number;
    name: string;
    match_type: 'exact' | 'partial';
  }>;
}

interface BulkUploadTableProps {
  files: BulkUploadFile[];
  accounts: Account[];
  onFileRemove: (fileId: string) => void;
  onAccountSelect: (fileId: string, accountId: number) => void;
  onDataTypeSelect: (fileId: string, dataType: DataType) => void;
  onUploadFile: (fileId: string) => Promise<void>;
  onRetryUpload: (fileId: string) => Promise<void>;
  onUploadAll: () => Promise<void>;
}

const BulkUploadTable: React.FC<BulkUploadTableProps> = ({
  files,
  accounts,
  onFileRemove,
  onAccountSelect,
  onDataTypeSelect,
  onUploadFile,
  onRetryUpload,
  onUploadAll
}) => {
  const [selectedFiles, setSelectedFiles] = useState<Set<string>>(new Set());
  const [mismatchDialog, setMismatchDialog] = useState<{
    open: boolean;
    fileId: string | null;
    fileName: string;
    detectedUsername: string;
    selectedAccountName: string;
    selectedAccountUsername?: string;
  }>({
    open: false,
    fileId: null,
    fileName: '',
    detectedUsername: '',
    selectedAccountName: '',
  });

  // Check if selected account matches detected username
  const checkAccountMatch = useCallback((file: BulkUploadFile): 'exact' | 'warning' | 'none' => {
    if (!file.selectedAccountId || !file.detectedUsername) {
      return 'none';
    }
    
    const selectedAccount = accounts.find(acc => acc.id === file.selectedAccountId);
    if (!selectedAccount) {
      return 'none';
    }
    
    const detectedLower = file.detectedUsername.toLowerCase();
    const platformUserLower = selectedAccount.platform_username?.toLowerCase() || '';
    
    // Exact match
    if (detectedLower === platformUserLower) {
      return 'exact';
    }
    
    // Partial match or no match (warning)
    if (platformUserLower.includes(detectedLower) || 
        detectedLower.includes(platformUserLower)) {
      return 'warning';
    }
    
    // No match - different user (warning)
    return 'warning';
  }, [accounts]);

  const getStatusChip = useCallback((file: BulkUploadFile) => {
    switch (file.status) {
      case 'pending':
        return (
          <Chip 
            label="Pending" 
            color="default" 
            size="small"
            icon={<UploadIcon />}
          />
        );
      case 'uploading':
        return (
          <Chip 
            label="Uploading" 
            color="primary" 
            size="small"
            icon={<UploadIcon />}
          />
        );
      case 'completed':
        return (
          <Chip 
            label="Completed" 
            color="success" 
            size="small"
            icon={<CheckCircleIcon />}
          />
        );
      case 'failed':
        return (
          <Chip 
            label="Failed" 
            color="error" 
            size="small"
            icon={<ErrorIcon />}
          />
        );
      default:
        return null;
    }
  }, []);

  const canUploadFile = useCallback((file: BulkUploadFile) => {
    return file.selectedAccountId && ['pending', 'failed'].includes(file.status);
  }, []);

  const canUploadAll = useCallback(() => {
    return files.some(file => canUploadFile(file));
  }, [files, canUploadFile]);

  const getAccountName = useCallback((accountId: number) => {
    const account = accounts.find(acc => acc.id === accountId);
    return account?.name || 'Unknown Account';
  }, [accounts]);

  const handleUploadClick = useCallback((fileItem: BulkUploadFile) => {
    const matchStatus = checkAccountMatch(fileItem);
    
    if (matchStatus === 'warning' && fileItem.detectedUsername && fileItem.selectedAccountId) {
      const selectedAccount = accounts.find(acc => acc.id === fileItem.selectedAccountId);
      
      if (selectedAccount) {
        // Show warning dialog for mismatched accounts
        setMismatchDialog({
          open: true,
          fileId: fileItem.id,
          fileName: fileItem.file.name,
          detectedUsername: fileItem.detectedUsername,
          selectedAccountName: selectedAccount.name,
          selectedAccountUsername: selectedAccount.platform_username || undefined,
        });
        return;
      }
    }
    
    // No mismatch or no detection - proceed with upload
    onUploadFile(fileItem.id);
  }, [checkAccountMatch, accounts, onUploadFile]);

  const handleMismatchConfirm = useCallback(() => {
    if (mismatchDialog.fileId) {
      onUploadFile(mismatchDialog.fileId);
    }
    setMismatchDialog(prev => ({ ...prev, open: false }));
  }, [mismatchDialog.fileId, onUploadFile]);

  const handleMismatchCancel = useCallback(() => {
    setMismatchDialog(prev => ({ ...prev, open: false }));
  }, []);

  const pendingCount = files.filter(f => f.status === 'pending').length;
  const uploadingCount = files.filter(f => f.status === 'uploading').length;
  const completedCount = files.filter(f => f.status === 'completed').length;
  const failedCount = files.filter(f => f.status === 'failed').length;

  if (files.length === 0) {
    return (
      <Alert severity="info" sx={{ mt: 2 }}>
        No files selected for bulk upload. Drop multiple CSV files above to get started.
      </Alert>
    );
  }

  return (
    <Box sx={{ mt: 3 }}>
      {/* Summary Header */}
      <Box sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 2, flexWrap: 'wrap' }}>
        <Typography variant="h6" sx={{ flexGrow: 1 }}>
          Bulk Upload Manager ({files.length} files)
        </Typography>
        
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Chip label={`${pendingCount} Pending`} color="default" size="small" />
          {uploadingCount > 0 && <Chip label={`${uploadingCount} Uploading`} color="primary" size="small" />}
          {completedCount > 0 && <Chip label={`${completedCount} Completed`} color="success" size="small" />}
          {failedCount > 0 && <Chip label={`${failedCount} Failed`} color="error" size="small" />}
        </Box>

        <Button
          variant="contained"
          startIcon={<UploadIcon />}
          onClick={onUploadAll}
          disabled={!canUploadAll() || uploadingCount > 0}
          size="small"
        >
          Upload All Ready
        </Button>
      </Box>

      {/* Files Table */}
      <TableContainer component={Paper} sx={{ maxHeight: 400, overflow: 'auto' }}>
        <Table stickyHeader size="small">
          <TableHead>
            <TableRow>
              <TableCell sx={{ minWidth: 200 }}>File Name</TableCell>
              <TableCell sx={{ minWidth: 180 }}>Account</TableCell>
              <TableCell sx={{ minWidth: 120 }}>Data Type</TableCell>
              <TableCell sx={{ minWidth: 100 }}>Detected User</TableCell>
              <TableCell sx={{ minWidth: 120 }}>Status</TableCell>
              <TableCell sx={{ minWidth: 150 }}>Progress</TableCell>
              <TableCell sx={{ minWidth: 120 }}>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {files.map((fileItem) => (
              <TableRow key={fileItem.id} hover>
                <TableCell>
                  <Box sx={{ display: 'flex', flexDirection: 'column' }}>
                    <Typography variant="body2" sx={{ fontWeight: 'medium' }}>
                      {fileItem.file.name}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {(fileItem.file.size / 1024).toFixed(1)} KB
                    </Typography>
                  </Box>
                </TableCell>

                <TableCell>
                  <FormControl 
                    size="small" 
                    sx={{ 
                      minWidth: 140,
                      '& .MuiOutlinedInput-root': {
                        borderColor: fileItem.selectedAccountId && fileItem.detectedUsername 
                          ? checkAccountMatch(fileItem) === 'exact' 
                            ? 'success.main' 
                            : checkAccountMatch(fileItem) === 'warning' 
                              ? 'warning.main' 
                              : 'inherit'
                          : 'inherit',
                      }
                    }}
                  >
                    <Select
                      value={fileItem.selectedAccountId || ''}
                      onChange={(e) => onAccountSelect(fileItem.id, Number(e.target.value))}
                      disabled={fileItem.status === 'uploading' || fileItem.status === 'completed'}
                      displayEmpty
                    >
                      <MenuItem value="">
                        <em>Select Account</em>
                      </MenuItem>
                      {accounts.map((account) => (
                        <MenuItem key={account.id} value={account.id}>
                          {account.name}
                          {account.platform_username && (
                            <Typography variant="caption" color="text.secondary" sx={{ ml: 1 }}>
                              ({account.platform_username})
                            </Typography>
                          )}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                  
                  {/* Account match indicator */}
                  {fileItem.selectedAccountId && fileItem.detectedUsername && (
                    <Box sx={{ mt: 0.5, display: 'flex', alignItems: 'center', gap: 0.5 }}>
                      {checkAccountMatch(fileItem) === 'exact' ? (
                        <Tooltip title="Perfect match! Detected username matches selected account">
                          <Chip
                            icon={<VerifiedUserIcon />}
                            label="Match"
                            size="small"
                            color="success"
                            variant="outlined"
                          />
                        </Tooltip>
                      ) : checkAccountMatch(fileItem) === 'warning' ? (
                        <Tooltip title="Warning: Detected username doesn't match selected account. This may cause data integrity issues.">
                          <Chip
                            icon={<WarningIcon />}
                            label="Mismatch"
                            size="small"
                            color="warning"
                            variant="outlined"
                          />
                        </Tooltip>
                      ) : null}
                    </Box>
                  )}
                  
                  {/* Show suggested accounts if available */}
                  {fileItem.suggestedAccounts.length > 0 && !fileItem.selectedAccountId && (
                    <Box sx={{ mt: 1 }}>
                      {fileItem.suggestedAccounts.slice(0, 2).map((suggestion) => (
                        <Tooltip 
                          key={suggestion.id}
                          title={`Click to select ${suggestion.name}`}
                        >
                          <Chip
                            label={suggestion.name}
                            size="small"
                            color={suggestion.match_type === 'exact' ? 'success' : 'warning'}
                            variant="outlined"
                            onClick={() => onAccountSelect(fileItem.id, suggestion.id)}
                            sx={{ mr: 0.5, mb: 0.5, cursor: 'pointer' }}
                          />
                        </Tooltip>
                      ))}
                    </Box>
                  )}
                </TableCell>

                <TableCell>
                  <FormControl size="small" sx={{ minWidth: 100 }}>
                    <Select
                      value={fileItem.dataType}
                      onChange={(e) => onDataTypeSelect(fileItem.id, e.target.value as DataType)}
                      disabled={fileItem.status === 'uploading' || fileItem.status === 'completed'}
                    >
                      {DATA_TYPE_OPTIONS.map((option) => (
                        <MenuItem key={option.value} value={option.value}>
                          {option.label}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </TableCell>

                <TableCell>
                  {fileItem.detectedUsername ? (
                    <Chip
                      label={fileItem.detectedUsername}
                      size="small"
                      color="primary"
                      variant="outlined"
                    />
                  ) : (
                    <Typography variant="caption" color="text.secondary">
                      Not detected
                    </Typography>
                  )}
                </TableCell>

                <TableCell>
                  {getStatusChip(fileItem)}
                </TableCell>

                <TableCell>
                  <Box sx={{ width: '100%' }}>
                    {fileItem.status === 'uploading' ? (
                      <Box>
                        <LinearProgress
                          variant="determinate"
                          value={fileItem.progress}
                          sx={{ mb: 0.5 }}
                        />
                        <Typography variant="caption" color="text.secondary">
                          {fileItem.progress}% - {fileItem.message || 'Processing...'}
                        </Typography>
                      </Box>
                    ) : fileItem.message ? (
                      <Typography 
                        variant="caption" 
                        color={fileItem.status === 'failed' ? 'error' : 'text.secondary'}
                        sx={{ display: 'block' }}
                      >
                        {fileItem.message}
                      </Typography>
                    ) : (
                      <Typography variant="caption" color="text.secondary">
                        {fileItem.selectedAccountId ? 'Ready to upload' : 'Select account first'}
                      </Typography>
                    )}
                  </Box>
                </TableCell>

                <TableCell>
                  <Box sx={{ display: 'flex', gap: 0.5 }}>
                    {canUploadFile(fileItem) && (
                      <Tooltip title="Upload this file">
                        <IconButton
                          size="small"
                          onClick={() => handleUploadClick(fileItem)}
                          color="primary"
                        >
                          <UploadIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    )}
                    
                    {fileItem.status === 'failed' && (
                      <Tooltip title="Retry upload">
                        <IconButton
                          size="small"
                          onClick={() => onRetryUpload(fileItem.id)}
                          color="warning"
                        >
                          <RefreshIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    )}

                    <Tooltip title="Remove file">
                      <IconButton
                        size="small"
                        onClick={() => onFileRemove(fileItem.id)}
                        color="error"
                        disabled={fileItem.status === 'uploading'}
                      >
                        <DeleteIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  </Box>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Bulk Operations */}
      {files.length > 1 && (
        <Box sx={{ mt: 2, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
            💡 <strong>Bulk Operations Tips:</strong>
          </Typography>
          <Typography variant="body2" color="text.secondary">
            • Use suggested account chips for quick selection
            <br />
            • Files with exact username matches will be prioritized
            <br />
            • Upload will process files sequentially to avoid server overload
            <br />
            • Failed uploads can be retried individually
          </Typography>
        </Box>
      )}
      
      {/* Account Mismatch Warning Dialog */}
      <AccountMismatchDialog
        open={mismatchDialog.open}
        onClose={handleMismatchCancel}
        onConfirm={handleMismatchConfirm}
        fileName={mismatchDialog.fileName}
        detectedUsername={mismatchDialog.detectedUsername}
        selectedAccountName={mismatchDialog.selectedAccountName}
        selectedAccountUsername={mismatchDialog.selectedAccountUsername}
      />
    </Box>
  );
};

export default BulkUploadTable;