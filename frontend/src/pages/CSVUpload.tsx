import React, { useState, useEffect, useCallback } from 'react';
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
} from '@mui/material';
import { CloudUpload, CheckCircle, Error } from '@mui/icons-material';
import { accountsAPI, csvAPI } from '../services/api';
import { csvUploadStyles } from '../styles/pages/csvUploadStyles';
import type { Account } from '../types';

interface UploadResult {
  success: boolean;
  message: string;
  details?: {
    inserted_count: number;
    duplicate_count: number;
    total_records: number;
  };
}

const CSVUpload: React.FC = () => {
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [selectedAccount, setSelectedAccount] = useState<number | ''>('');
  const [dataType, setDataType] = useState<'order' | 'listing'>('order');
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState<UploadResult | null>(null);

  useEffect(() => {
    loadAccounts();
  }, []);

  const loadAccounts = async () => {
    try {
      const accountsData = await accountsAPI.getAccounts();
      setAccounts(accountsData);
      if (accountsData.length > 0) {
        setSelectedAccount(accountsData[0].id);
      }
    } catch (error) {
      console.error('Failed to load accounts:', error);
    }
  };

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    if (!selectedAccount || acceptedFiles.length === 0) return;

    const file = acceptedFiles[0];
    setUploading(true);
    setUploadResult(null);

    try {
      const result = await csvAPI.uploadCSV(file, selectedAccount as number, dataType);
      setUploadResult({
        success: true,
        message: 'File uploaded successfully!',
        details: result,
      });
    } catch (error: any) {
      setUploadResult({
        success: false,
        message: error.response?.data?.detail || 'Upload failed',
      });
    } finally {
      setUploading(false);
    }
  }, [selectedAccount, dataType]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/csv': ['.csv'],
      'application/vnd.ms-excel': ['.csv'],
    },
    maxFiles: 1,
    disabled: !selectedAccount || uploading,
  });

  return (
    <Box>
      <Typography variant="h4" component="h1" sx={csvUploadStyles.pageTitle}>
        CSV Upload
      </Typography>

      {/* Upload Configuration */}
      <Box sx={csvUploadStyles.configContainer}>
        <FormControl sx={csvUploadStyles.accountSelect}>
          <InputLabel>eBay Account</InputLabel>
          <Select
            value={selectedAccount}
            label="eBay Account"
            onChange={(e) => setSelectedAccount(e.target.value as number | '')}
          >
            {accounts.map((account) => (
              <MenuItem key={account.id} value={account.id}>
                {account.name}
              </MenuItem>
            ))}
          </Select>
        </FormControl>

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
            sx={csvUploadStyles.dropzoneArea(!!selectedAccount, uploading, isDragActive)}
          >
            <input {...getInputProps()} />
            
            {uploading ? (
              <Box>
                <CircularProgress sx={csvUploadStyles.progressSpinner} />
                <Typography variant="h6">
                  Uploading CSV file...
                </Typography>
              </Box>
            ) : (
              <Box>
                <CloudUpload sx={csvUploadStyles.cloudIcon} />
                <Typography variant="h6" sx={csvUploadStyles.uploadTitle}>
                  {isDragActive
                    ? 'Drop the CSV file here'
                    : 'Drag & drop a CSV file here, or click to select'
                  }
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  Only CSV files are accepted
                </Typography>
                {!selectedAccount && (
                  <Typography variant="body2" color="error" sx={csvUploadStyles.accountErrorText}>
                    Please select an eBay account first
                  </Typography>
                )}
              </Box>
            )}
          </Box>
        </CardContent>
      </Card>

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