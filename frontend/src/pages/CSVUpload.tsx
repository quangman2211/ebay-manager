import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import {
  Box,
  Typography,
  Card,
  CardContent,
  CircularProgress,
} from '@mui/material';
import { CloudUpload } from '@mui/icons-material';
import { useAccount } from '../context/AccountContext';
import { csvAPI } from '../services/api';
import { csvUploadStyles } from '../styles/pages/csvUploadStyles';
// REMOVED: ProgressBar and ErrorRecoveryPanel components (single upload mode removed)
import BulkUploadTable, { BulkUploadFile } from '../components/Upload/BulkUploadTable';
import type { Account } from '../types';
import { DataType, DEFAULT_DATA_TYPE } from '../constants/dataTypes';
import { getAllInstructionSections } from '../constants/instructions';

/* REMOVED: Interfaces for single upload mode
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
  platform_username: string | null;
  match_type: 'exact' | 'partial';
}

interface SuggestionState {
  detecting: boolean;
  detectedUsername: string | undefined;
  suggestions: AccountSuggestion[];
  totalSuggestions: number;
  showSuggestions: boolean;
}

interface EnhancedUploadState {
  active: boolean;
  uploadId: string | null;
  filename: string | null;
  state: 'processing' | 'completed' | 'failed' | 'cancelled';
  message: string;
  progressPercent: number;
  startedAt: string | null;
  error: {
    code: string;
    message: string;
    suggestions: string[];
  } | null;
  retryCount: number;
  maxRetries: number;
}

interface ProgressTrackingState {
  intervalId: NodeJS.Timeout | null;
  lastUpdate: number;
  isPolling: boolean;
}
*/

const CSVUpload: React.FC = () => {
  const { state: accountState, dispatch } = useAccount();
  const [bulkFiles, setBulkFiles] = useState<BulkUploadFile[]>([]);
  
  // Keep minimal state needed for drag & drop area
  const [detecting, setDetecting] = useState(false);

  /* DISABLED - Progress tracking state for single upload mode
  const [progressTracking, setProgressTracking] = useState<ProgressTrackingState>({
    intervalId: null,
    lastUpdate: Date.now(),
    isPolling: false,
  });
  */

  /* DISABLED - Progress tracking functions for single upload mode
  const startProgressPolling = useCallback((uploadId: string) => {
    if (progressTracking.isPolling) return;

    setProgressTracking(prev => ({ ...prev, isPolling: true }));
    
    const intervalId = setInterval(async () => {
      try {
        const progressData = await csvAPI.getUploadProgress(uploadId);
        
        if (progressData.success && progressData.upload_id) {
          setEnhancedUpload(prev => ({
            ...prev,
            state: progressData.state || 'processing',
            message: progressData.message || 'Processing...',
            progressPercent: progressData.progress_percent || 0,
            startedAt: progressData.started_at || prev.startedAt,
          }));

          // Stop polling if upload is complete or failed
          if (progressData.state === 'completed' || progressData.state === 'failed') {
            clearInterval(intervalId);
            setProgressTracking(prev => ({ 
              ...prev, 
              intervalId: null, 
              isPolling: false 
            }));
          }
        } else if (!progressData.success && progressData.error) {
          // Upload not found or error occurred
          clearInterval(intervalId);
          setProgressTracking(prev => ({ 
            ...prev, 
            intervalId: null, 
            isPolling: false 
          }));
        }
        
        setProgressTracking(prev => ({ ...prev, lastUpdate: Date.now() }));
      } catch (error) {
        console.error('Progress polling error:', error);
      }
    }, 500); // Poll every 500ms

    setProgressTracking(prev => ({ ...prev, intervalId }));
  }, [progressTracking.isPolling]);

  const stopProgressPolling = useCallback(() => {
    if (progressTracking.intervalId) {
      clearInterval(progressTracking.intervalId);
      setProgressTracking({
        intervalId: null,
        lastUpdate: Date.now(),
        isPolling: false,
      });
    }
  }, [progressTracking.intervalId]);
  */

  // Enhanced upload function with progress tracking and fallback
  /* DISABLED - Single Upload Mode Removed
  const handleEnhancedUpload = useCallback(async (file: File, accountId: number, retryAttempt = 0) => {
    try {
      setUploading(true);
      setEnhancedUpload(prev => ({
        ...prev,
        active: true,
        filename: file.name,
        state: 'processing',
        message: 'Starting upload...',
        progressPercent: 0,
        startedAt: new Date().toISOString(),
        error: null,
        retryCount: retryAttempt,
      }));

      // Try enhanced upload first
      const result = await csvAPI.uploadCSVEnhanced(file, accountId, 'order'); // dataType removed

      if (result.success && result.upload_id) {
        // Start progress tracking
        setEnhancedUpload(prev => ({
          ...prev,
          uploadId: result.upload_id || null,
          message: result.message || 'Processing upload...',
        }));
        
        startProgressPolling(result.upload_id);

        // Set successful result when upload completes
        setUploadResult({
          success: true,
          message: result.message,
          details: {
            inserted_count: result.inserted_count || 0,
            duplicate_count: result.duplicate_count || 0,
            total_records: result.total_records || 0,
            detected_platform_username: result.detected_username,
          },
        });
      } else {
        // Enhanced upload failed, set error state
        setEnhancedUpload(prev => ({
          ...prev,
          state: 'failed',
          message: result.message || 'Upload failed',
          error: result.error || null,
        }));

        setUploadResult({
          success: false,
          message: result.message || 'Upload failed',
        });
      }
    } catch (error: any) {
      console.error('Enhanced upload failed:', error);
      
      // If enhanced upload fails completely, try fallback to original upload
      if (retryAttempt === 0) {
        try {
          setEnhancedUpload(prev => ({
            ...prev,
            message: 'Enhanced upload unavailable, falling back to standard upload...',
            progressPercent: 50,
          }));

          const fallbackResult = await csvAPI.uploadCSV(file, accountId, 'order'); // dataType removed
          
          setEnhancedUpload(prev => ({
            ...prev,
            state: 'completed',
            message: 'Upload completed (fallback mode)',
            progressPercent: 100,
          }));

          setUploadResult({
            success: true,
            message: 'File uploaded successfully (fallback mode)',
            details: {
              inserted_count: fallbackResult.inserted_count || 0,
              duplicate_count: fallbackResult.duplicate_count || 0,
              total_records: fallbackResult.total_records || 0,
              detected_platform_username: fallbackResult.detected_platform_username,
            },
          });
        } catch (fallbackError: any) {
          // Both enhanced and fallback failed
          const errorMessage = fallbackError.response?.data?.detail || 'Upload failed';
          setEnhancedUpload(prev => ({
            ...prev,
            state: 'failed',
            message: errorMessage,
            error: {
              code: 'UPLOAD_ERROR',
              message: errorMessage,
              suggestions: ['Check your internet connection', 'Verify file format', 'Try again later', 'Contact support if problem persists'],
            },
          }));

          setUploadResult({
            success: false,
            message: errorMessage,
          });
        }
      } else {
        // Retry attempt failed
        const errorMessage = error.response?.data?.detail || 'Upload failed';
        setEnhancedUpload(prev => ({
          ...prev,
          state: 'failed',
          message: errorMessage,
          error: {
            code: 'UPLOAD_ERROR',
            message: errorMessage,
            suggestions: ['Check your internet connection', 'Verify file format', 'Try again later', 'Contact support if problem persists'],
          },
        }));

        setUploadResult({
          success: false,
          message: errorMessage,
        });
      }
    } finally {
      setUploading(false);
    }
  }, [startProgressPolling]); // dataType dependency removed

  /* DISABLED - Cleanup effect for single upload mode
  useEffect(() => {
    return () => {
      stopProgressPolling();
    };
  }, [stopProgressPolling]);
  */

  /* DISABLED - Error recovery functions for single upload mode
  const handleRetryUpload = useCallback(() => {
    if (!currentFile || !accountState.currentAccount?.id || enhancedUpload.retryCount >= enhancedUpload.maxRetries) {
      return;
    }

    // Reset error state and retry
    setEnhancedUpload(prev => ({
      ...prev,
      error: null,
      state: 'processing',
      message: 'Retrying upload...',
    }));

    // Add exponential backoff delay
    const delay = Math.min(1000 * Math.pow(2, enhancedUpload.retryCount), 5000);
    setTimeout(() => {
      handleEnhancedUpload(currentFile, accountState.currentAccount!.id, enhancedUpload.retryCount + 1);
    }, delay);
  }, [currentFile, accountState.currentAccount?.id, enhancedUpload.retryCount, enhancedUpload.maxRetries, handleEnhancedUpload]);

  const handleCancelUpload = useCallback(() => {
    stopProgressPolling();
    setEnhancedUpload(prev => ({
      ...prev,
      active: false,
      state: 'cancelled',
      message: 'Upload cancelled',
      error: null,
    }));
    setUploading(false);
    setCurrentFile(null);
  }, [stopProgressPolling]);
  */

  // Bulk Upload Functions
  const generateFileId = useCallback(() => {
    return `file_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }, []);

  const handleBulkFileAdd = useCallback(async (files: File[]) => {
    setDetecting(true);
    const newBulkFiles: BulkUploadFile[] = [];
    
    try {
      for (const file of files) {
      const fileId = generateFileId();
      
      // Get account suggestions for this file
      try {
        const suggestionResult = await csvAPI.suggestAccountsForCSV(file);
        
        const bulkFile: BulkUploadFile = {
          id: fileId,
          file: file,
          status: 'pending',
          progress: 0,
          dataType: DEFAULT_DATA_TYPE,
          detectedUsername: suggestionResult.detected_username || undefined,
          suggestedAccounts: suggestionResult.suggested_accounts.map(acc => ({
            id: acc.id,
            name: acc.name,
            match_type: acc.match_type
          })),
        };

        // Auto-select if there's exactly one exact match
        const exactMatches = suggestionResult.suggested_accounts.filter(acc => acc.match_type === 'exact');
        if (exactMatches.length === 1) {
          bulkFile.selectedAccountId = exactMatches[0].id;
        }

        newBulkFiles.push(bulkFile);
      } catch (error) {
        console.error('Failed to get suggestions for file:', file.name, error);
        newBulkFiles.push({
          id: fileId,
          file: file,
          status: 'pending',
          progress: 0,
          dataType: DEFAULT_DATA_TYPE,
          suggestedAccounts: [],
        });
      }
      }
    
      setBulkFiles(prev => [...prev, ...newBulkFiles]);
    } finally {
      setDetecting(false);
    }
  }, [generateFileId]);

  const handleBulkFileRemove = useCallback((fileId: string) => {
    setBulkFiles(prev => prev.filter(f => f.id !== fileId));
  }, []);

  const handleBulkAccountSelect = useCallback((fileId: string, accountId: number) => {
    setBulkFiles(prev => prev.map(file => 
      file.id === fileId 
        ? { ...file, selectedAccountId: accountId }
        : file
    ));
  }, []);

  const handleBulkDataTypeSelect = useCallback((fileId: string, dataType: DataType) => {
    setBulkFiles(prev => prev.map(file => 
      file.id === fileId 
        ? { ...file, dataType: dataType }
        : file
    ));
  }, []);

  const handleBulkFileUpload = useCallback(async (fileId: string) => {
    const fileItem = bulkFiles.find(f => f.id === fileId);
    if (!fileItem || !fileItem.selectedAccountId) return;

    // Update status to uploading
    setBulkFiles(prev => prev.map(file => 
      file.id === fileId 
        ? { ...file, status: 'uploading', progress: 0, message: 'Starting upload...' }
        : file
    ));

    try {
      // Use enhanced upload with per-file data type
      const result = await csvAPI.uploadCSVEnhanced(fileItem.file, fileItem.selectedAccountId, fileItem.dataType);
      
      if (result.success) {
        setBulkFiles(prev => prev.map(file => 
          file.id === fileId 
            ? { 
                ...file, 
                status: 'completed', 
                progress: 100,
                message: `Upload successful: ${result.inserted_count || 0} records`
              }
            : file
        ));
      } else {
        setBulkFiles(prev => prev.map(file => 
          file.id === fileId 
            ? { 
                ...file, 
                status: 'failed', 
                progress: 0,
                message: result.message || 'Upload failed'
              }
            : file
        ));
      }
    } catch (error: any) {
      setBulkFiles(prev => prev.map(file => 
        file.id === fileId 
          ? { 
              ...file, 
              status: 'failed', 
              progress: 0,
              message: error.message || 'Upload failed'
            }
          : file
      ));
    }
  }, [bulkFiles]);

  const handleBulkRetryUpload = useCallback(async (fileId: string) => {
    await handleBulkFileUpload(fileId);
  }, [handleBulkFileUpload]);

  const handleBulkUploadAll = useCallback(async () => {
    const readyFiles = bulkFiles.filter(file => 
      file.selectedAccountId && ['pending', 'failed'].includes(file.status)
    );

    // Upload files sequentially to avoid overwhelming the server
    for (const file of readyFiles) {
      await handleBulkFileUpload(file.id);
      // Small delay between uploads
      await new Promise(resolve => setTimeout(resolve, 500));
    }
  }, [bulkFiles, handleBulkFileUpload]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop: useCallback(async (acceptedFiles: File[]) => {
      if (acceptedFiles.length === 0) return;

      // Always use bulk upload mode (single upload mode removed)
      await handleBulkFileAdd(acceptedFiles);
    }, [
      handleBulkFileAdd
    ]),
    accept: {
      'text/csv': ['.csv'],
      'application/vnd.ms-excel': ['.csv'],
    },
    maxFiles: 10,
    multiple: true,
    disabled: detecting,
  });

  return (
    <Box>
      <Typography variant="h4" component="h1" sx={csvUploadStyles.pageTitle}>
        CSV Upload
      </Typography>

      {/* Data Type selection moved to individual file level in table */}

      {/* Upload Area */}
      <Card sx={csvUploadStyles.uploadCard}>
        <CardContent>
          <Box
            {...getRootProps()}
            sx={csvUploadStyles.dropzoneArea(false, detecting, isDragActive)}
          >
            <input {...getInputProps()} />
            
            {detecting ? (
              <Box>
                <CircularProgress sx={csvUploadStyles.progressSpinner} />
                <Typography variant="h6">
                  Processing CSV files...
                </Typography>
              </Box>
            ) : (
              <Box>
                <CloudUpload sx={csvUploadStyles.cloudIcon} />
                <Typography variant="h6" sx={csvUploadStyles.uploadTitle}>
                  {isDragActive
                    ? 'Drop the CSV files here'
                    : 'Drag & drop CSV files here, or click to select (up to 10 files)'
                  }
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  Only CSV files are accepted
                </Typography>
                <Typography variant="body2" color="primary" sx={csvUploadStyles.accountErrorText}>
                  🚀 Upload CSV files with automatic account matching and progress tracking!
                </Typography>
              </Box>
            )}
          </Box>
        </CardContent>
      </Card>

      {/* Upload Files Table */}
      <BulkUploadTable
        files={bulkFiles}
        accounts={accountState.accounts}
        onFileRemove={handleBulkFileRemove}
        onAccountSelect={handleBulkAccountSelect}
        onDataTypeSelect={handleBulkDataTypeSelect}
        onUploadFile={handleBulkFileUpload}
        onRetryUpload={handleBulkRetryUpload}
        onUploadAll={handleBulkUploadAll}
      />


      {/* REMOVED - Account Suggestions popup (single upload mode removed) */}

      {/* REMOVED - Upload result alert (single upload mode removed) */}

      {/* Instructions */}
      <Card>
        <CardContent>
          <Typography variant="h6" sx={csvUploadStyles.instructionsTitle}>
            Instructions
          </Typography>
          
          {getAllInstructionSections().map((section, index) => (
            <React.Fragment key={section.title}>
              <Typography variant="body2" sx={csvUploadStyles.instructionText}>
                <strong>{section.title}</strong>
              </Typography>
              <Typography 
                variant="body2" 
                sx={
                  index === getAllInstructionSections().length - 1 
                    ? csvUploadStyles.finalInstructionText 
                    : csvUploadStyles.instructionDetails
                }
              >
                {section.details.map((detail, detailIndex) => (
                  <React.Fragment key={detailIndex}>
                    • {detail}
                    {detailIndex < section.details.length - 1 && <br />}
                  </React.Fragment>
                ))}
              </Typography>
            </React.Fragment>
          ))}
        </CardContent>
      </Card>
    </Box>
  );
};

export default CSVUpload;