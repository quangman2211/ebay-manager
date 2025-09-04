import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import {
  Box,
  Typography,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Card,
  CardContent,
  Button,
  Alert,
  CircularProgress,
  Chip,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  ListItemButton,
  Divider,
  Badge,
} from '@mui/material';
import { CloudUpload, CheckCircle, Error, AccountCircle, Person, Stars } from '@mui/icons-material';
import { useAccount } from '../context/AccountContext';
import { csvAPI, accountsAPI } from '../services/api';
import { csvUploadStyles } from '../styles/pages/csvUploadStyles';
import type { Account } from '../types';

interface UploadResult {
  success: boolean;
  message: string;
  details?: {
    inserted_count: number;
    duplicate_count: number;
    total_records: number;
    detected_platform_username?: string;
  };
}

interface AccountSuggestion {
  id: number;
  name: string;
  ebay_username: string | null;
  platform_username: string | null;
  match_type: 'exact' | 'partial';
}

interface SuggestionState {
  detecting: boolean;
  detectedUsername: string | null;
  suggestions: AccountSuggestion[];
  totalSuggestions: number;
  showSuggestions: boolean;
}

const CSVUpload: React.FC = () => {
  const { state: accountState, dispatch } = useAccount();
  const [dataType, setDataType] = useState<'order' | 'listing'>('order');
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState<UploadResult | null>(null);
  const [currentFile, setCurrentFile] = useState<File | null>(null);
  const [suggestionState, setSuggestionState] = useState<SuggestionState>({
    detecting: false,
    detectedUsername: null,
    suggestions: [],
    totalSuggestions: 0,
    showSuggestions: false,
  });

  const handleAccountSuggestions = useCallback(async (file: File) => {
    setSuggestionState(prev => ({ ...prev, detecting: true, showSuggestions: false }));
    setUploadResult(null);
    
    try {
      const suggestionResult = await csvAPI.suggestAccountsForCSV(file);
      setSuggestionState({
        detecting: false,
        detectedUsername: suggestionResult.detected_username,
        suggestions: suggestionResult.suggested_accounts,
        totalSuggestions: suggestionResult.total_suggestions,
        showSuggestions: suggestionResult.suggested_accounts.length > 0,
      });
    } catch (error: any) {
      setSuggestionState({
        detecting: false,
        detectedUsername: null,
        suggestions: [],
        totalSuggestions: 0,
        showSuggestions: false,
      });
      console.error('Failed to get account suggestions:', error);
    }
  }, []);

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    if (acceptedFiles.length === 0) return;

    const file = acceptedFiles[0];
    setCurrentFile(file);
    setUploadResult(null);

    // If no account is selected, show suggestions
    if (!accountState.currentAccount?.id) {
      await handleAccountSuggestions(file);
      return;
    }

    // Proceed with upload if account is selected
    await uploadCSVFile(file, accountState.currentAccount.id);
  }, [accountState.currentAccount?.id, handleAccountSuggestions]);

  const uploadCSVFile = useCallback(async (file: File, accountId: number) => {
    setUploading(true);
    setUploadResult(null);

    try {
      const result = await csvAPI.uploadCSV(file, accountId, dataType);
      setUploadResult({
        success: true,
        message: 'File uploaded successfully!',
        details: result,
      });
      
      // Clear suggestions after successful upload
      setSuggestionState({
        detecting: false,
        detectedUsername: null,
        suggestions: [],
        totalSuggestions: 0,
        showSuggestions: false,
      });
      setCurrentFile(null);
    } catch (error: any) {
      setUploadResult({
        success: false,
        message: error.response?.data?.detail || 'Upload failed',
      });
    } finally {
      setUploading(false);
    }
  }, [dataType]);

  const handleSuggestedAccountSelect = useCallback(async (suggestion: AccountSuggestion) => {
    // Find the full account from accounts list
    const fullAccount = accountState.accounts.find(acc => acc.id === suggestion.id);
    if (!fullAccount || !currentFile) return;

    // Switch to the suggested account
    dispatch({ type: 'SET_CURRENT_ACCOUNT', payload: fullAccount });
    
    // Upload the file
    await uploadCSVFile(currentFile, suggestion.id);
  }, [accountState.accounts, currentFile, dispatch, uploadCSVFile]);

  const handleManualAccountSelect = useCallback(() => {
    setSuggestionState(prev => ({ ...prev, showSuggestions: false }));
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/csv': ['.csv'],
      'application/vnd.ms-excel': ['.csv'],
    },
    maxFiles: 1,
    disabled: uploading || suggestionState.detecting,
  });

  return (
    <Box>
      <Typography variant="h4" component="h1" sx={csvUploadStyles.pageTitle}>
        CSV Upload
      </Typography>

      {/* Upload Configuration */}
      <Box sx={csvUploadStyles.configContainer}>
        <FormControl sx={csvUploadStyles.dataTypeSelect}>
          <InputLabel>Data Type</InputLabel>
          <Select
            value={dataType}
            label="Data Type"
            onChange={(e) => setDataType(e.target.value as 'order' | 'listing')}
          >
            <MenuItem value="order">Orders</MenuItem>
            <MenuItem value="listing">Listings</MenuItem>
          </Select>
        </FormControl>
      </Box>

      {/* Upload Area */}
      <Card sx={csvUploadStyles.uploadCard}>
        <CardContent>
          <Box
            {...getRootProps()}
            sx={csvUploadStyles.dropzoneArea(true, uploading || suggestionState.detecting, isDragActive)}
          >
            <input {...getInputProps()} />
            
            {uploading ? (
              <Box>
                <CircularProgress sx={csvUploadStyles.progressSpinner} />
                <Typography variant="h6">
                  Uploading CSV file...
                </Typography>
              </Box>
            ) : suggestionState.detecting ? (
              <Box>
                <CircularProgress sx={csvUploadStyles.progressSpinner} />
                <Typography variant="h6">
                  Analyzing CSV file for account suggestions...
                </Typography>
              </Box>
            ) : (
              <Box>
                <CloudUpload sx={csvUploadStyles.cloudIcon} />
                <Typography variant="h6" sx={csvUploadStyles.uploadTitle}>
                  {isDragActive
                    ? 'Drop the CSV file here'
                    : accountState.currentAccount?.id
                    ? 'Drag & drop a CSV file here, or click to select'
                    : 'Drag & drop a CSV file - we\'ll suggest matching accounts'
                  }
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  Only CSV files are accepted
                </Typography>
                {!accountState.currentAccount?.id && !suggestionState.showSuggestions && (
                  <Typography variant="body2" color="primary" sx={csvUploadStyles.accountErrorText}>
                    💡 Smart Upload: Drop a CSV file and we'll detect your eBay username to suggest matching accounts!
                  </Typography>
                )}
              </Box>
            )}
          </Box>
        </CardContent>
      </Card>

      {/* Account Suggestions */}
      {suggestionState.showSuggestions && (
        <Card sx={{ mt: 2, border: '2px solid', borderColor: 'primary.main' }}>
          <CardContent>
            <Typography variant="h6" sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
              <Stars color="primary" />
              Account Suggestions
              {suggestionState.detectedUsername && (
                <Chip
                  label={`Detected: ${suggestionState.detectedUsername}`}
                  size="small"
                  color="primary"
                  variant="outlined"
                />
              )}
            </Typography>
            
            {suggestionState.suggestions.length > 0 ? (
              <Box>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  We found {suggestionState.totalSuggestions} matching account{suggestionState.totalSuggestions !== 1 ? 's' : ''}. Click on an account to upload the CSV file:
                </Typography>
                
                <List>
                  {suggestionState.suggestions.map((suggestion, index) => (
                    <React.Fragment key={suggestion.id}>
                      <ListItem disablePadding>
                        <ListItemButton 
                          onClick={() => handleSuggestedAccountSelect(suggestion)}
                          sx={{
                            border: '1px solid',
                            borderColor: suggestion.match_type === 'exact' ? 'success.main' : 'warning.main',
                            borderRadius: 1,
                            mb: 1,
                            '&:hover': {
                              backgroundColor: suggestion.match_type === 'exact' ? 'success.50' : 'warning.50',
                            },
                          }}
                        >
                          <ListItemIcon>
                            <Badge 
                              badgeContent={suggestion.match_type === 'exact' ? '✓' : '~'} 
                              color={suggestion.match_type === 'exact' ? 'success' : 'warning'}
                            >
                              <AccountCircle color={suggestion.match_type === 'exact' ? 'success' : 'warning'} />
                            </Badge>
                          </ListItemIcon>
                          <ListItemText
                            primary={
                              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>
                                  {suggestion.name}
                                </Typography>
                                <Chip
                                  label={suggestion.match_type === 'exact' ? 'Exact Match' : 'Partial Match'}
                                  size="small"
                                  color={suggestion.match_type === 'exact' ? 'success' : 'warning'}
                                  variant="outlined"
                                />
                              </Box>
                            }
                            secondary={
                              <Box>
                                {suggestion.ebay_username && (
                                  <Typography variant="body2" color="text.secondary">
                                    eBay Username: {suggestion.ebay_username}
                                  </Typography>
                                )}
                                {suggestion.platform_username && (
                                  <Typography variant="body2" color="text.secondary">
                                    Platform ID: {suggestion.platform_username}
                                  </Typography>
                                )}
                              </Box>
                            }
                          />
                        </ListItemButton>
                      </ListItem>
                      {index < suggestionState.suggestions.length - 1 && <Divider />}
                    </React.Fragment>
                  ))}
                </List>
                
                <Box sx={{ mt: 2, display: 'flex', justifyContent: 'center' }}>
                  <Button
                    variant="text"
                    onClick={handleManualAccountSelect}
                    sx={{ textTransform: 'none' }}
                  >
                    Or select account manually from dropdown above
                  </Button>
                </Box>
              </Box>
            ) : (
              <Box>
                <Typography variant="body2" color="text.secondary">
                  No matching accounts found. Please select an account manually from the dropdown above.
                </Typography>
                <Box sx={{ mt: 2, display: 'flex', justifyContent: 'center' }}>
                  <Button
                    variant="outlined"
                    onClick={handleManualAccountSelect}
                  >
                    Select Account Manually
                  </Button>
                </Box>
              </Box>
            )}
          </CardContent>
        </Card>
      )}

      {/* Upload Result */}
      {uploadResult && (
        <Alert 
          severity={uploadResult.success ? 'success' : 'error'}
          icon={uploadResult.success ? <CheckCircle /> : <Error />}
          sx={csvUploadStyles.resultAlert}
        >
          <Typography variant="body1" sx={csvUploadStyles.resultMessage(!!uploadResult.details)}>
            {uploadResult.message}
          </Typography>
          
          {uploadResult.details && (
            <Box sx={csvUploadStyles.chipContainer}>
              <Chip 
                label={`${uploadResult.details.inserted_count} new records`}
                color="success"
                size="small"
              />
              {uploadResult.details.duplicate_count > 0 && (
                <Chip 
                  label={`${uploadResult.details.duplicate_count} duplicates skipped`}
                  color="warning"
                  size="small"
                />
              )}
              <Chip 
                label={`${uploadResult.details.total_records} total processed`}
                color="info"
                size="small"
              />
              {uploadResult.details.detected_platform_username && (
                <Chip 
                  label={`Auto-detected: ${uploadResult.details.detected_platform_username}`}
                  color="primary"
                  size="small"
                  variant="outlined"
                />
              )}
            </Box>
          )}
        </Alert>
      )}

      {/* Instructions */}
      <Card>
        <CardContent>
          <Typography variant="h6" sx={csvUploadStyles.instructionsTitle}>
            Instructions
          </Typography>
          
          <Typography variant="body2" sx={csvUploadStyles.instructionText}>
            <strong>🚀 Smart Upload Feature:</strong>
          </Typography>
          <Typography variant="body2" sx={csvUploadStyles.instructionDetails}>
            • Drop a CSV file without selecting an account first
            <br />
            • The system will automatically detect your eBay username from the CSV
            <br />
            • Matching accounts will be suggested based on detected username
            <br />
            • Click on a suggested account to upload instantly
          </Typography>

          <Typography variant="body2" sx={csvUploadStyles.instructionText}>
            <strong>For Orders:</strong>
          </Typography>
          <Typography variant="body2" sx={csvUploadStyles.instructionDetails}>
            • Export orders from eBay Seller Hub → Orders → Export to CSV
            <br />
            • The system will automatically detect duplicate orders and skip them
            <br />
            • New orders will be imported with "pending" status
          </Typography>
          
          <Typography variant="body2" sx={csvUploadStyles.instructionText}>
            <strong>For Listings:</strong>
          </Typography>
          <Typography variant="body2" sx={csvUploadStyles.finalInstructionText}>
            • Export listings from eBay Seller Hub → Listings → Export to CSV
            <br />
            • The system will update inventory levels and listing information
            <br />
            • Existing listings will be updated with new data
          </Typography>
        </CardContent>
      </Card>
    </Box>
  );
};

export default CSVUpload;