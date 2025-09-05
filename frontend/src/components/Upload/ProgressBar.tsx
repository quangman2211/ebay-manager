import React from 'react';
import {
  Box,
  LinearProgress,
  Typography,
  Chip,
  Card,
  CardContent,
} from '@mui/material';
import { CheckCircle, Error, Sync, Cancel } from '@mui/icons-material';

interface ProgressBarProps {
  uploadId?: string;
  filename?: string;
  state: 'processing' | 'completed' | 'failed' | 'cancelled';
  message: string;
  progressPercent: number;
  startedAt?: string;
  onCancel?: () => void;
  showCancel?: boolean;
}

const ProgressBar: React.FC<ProgressBarProps> = ({
  uploadId,
  filename,
  state,
  message,
  progressPercent,
  startedAt,
  onCancel,
  showCancel = true,
}) => {
  const getStateColor = () => {
    switch (state) {
      case 'completed':
        return 'success';
      case 'failed':
        return 'error';
      case 'cancelled':
        return 'default';
      default:
        return 'primary';
    }
  };

  const getStateIcon = () => {
    switch (state) {
      case 'completed':
        return <CheckCircle color="success" />;
      case 'failed':
        return <Error color="error" />;
      case 'cancelled':
        return <Cancel color="disabled" />;
      default:
        return <Sync color="primary" className="rotating" />;
    }
  };

  const formatElapsedTime = () => {
    if (!startedAt) return '';
    const elapsed = Date.now() - new Date(startedAt).getTime();
    const seconds = Math.floor(elapsed / 1000);
    const minutes = Math.floor(seconds / 60);
    if (minutes > 0) {
      return `${minutes}m ${seconds % 60}s`;
    }
    return `${seconds}s`;
  };

  const estimateTimeRemaining = () => {
    if (state !== 'processing' || progressPercent === 0 || !startedAt) return '';
    const elapsed = Date.now() - new Date(startedAt).getTime();
    const rate = progressPercent / elapsed;
    const remaining = (100 - progressPercent) / rate;
    const remainingSeconds = Math.floor(remaining / 1000);
    const remainingMinutes = Math.floor(remainingSeconds / 60);
    
    if (remainingMinutes > 0) {
      return `~${remainingMinutes}m ${remainingSeconds % 60}s remaining`;
    }
    return `~${remainingSeconds}s remaining`;
  };

  return (
    <Card sx={{ 
      border: '2px solid', 
      borderColor: `${getStateColor()}.main`,
      mb: 2 
    }}>
      <CardContent>
        {/* Header */}
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            {getStateIcon()}
            <Typography variant="h6">
              Upload Progress
            </Typography>
            <Chip
              label={state.charAt(0).toUpperCase() + state.slice(1)}
              color={getStateColor() as 'success' | 'error' | 'default' | 'primary'}
              size="small"
              variant="outlined"
            />
          </Box>
          
          {showCancel && state === 'processing' && onCancel && (
            <Chip
              label="Cancel"
              color="default"
              size="small"
              onClick={onCancel}
              clickable
              deleteIcon={<Cancel />}
              onDelete={onCancel}
            />
          )}
        </Box>

        {/* File Info */}
        {filename && (
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            File: <strong>{filename}</strong>
            {uploadId && (
              <> • ID: <code style={{ fontSize: '0.8em' }}>{uploadId.slice(0, 8)}...</code></>
            )}
          </Typography>
        )}

        {/* Progress Bar */}
        <Box sx={{ width: '100%', mb: 2 }}>
          <LinearProgress
            variant={state === 'processing' ? 'determinate' : 'determinate'}
            value={Math.min(progressPercent, 100)}
            color={getStateColor() as 'primary' | 'secondary' | 'inherit'}
            sx={{ 
              height: 8, 
              borderRadius: 4,
              '& .MuiLinearProgress-bar': {
                borderRadius: 4,
                transition: 'transform 0.5s ease',
              }
            }}
          />
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 1 }}>
            <Typography variant="body2" color="text.secondary">
              {Math.round(progressPercent)}%
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {estimateTimeRemaining()}
            </Typography>
          </Box>
        </Box>

        {/* Status Message */}
        <Typography 
          variant="body2" 
          color={state === 'failed' ? 'error.main' : 'text.primary'}
          sx={{ mb: 1 }}
        >
          {message}
        </Typography>

        {/* Timing Info */}
        {startedAt && (
          <Typography variant="caption" color="text.secondary">
            {state === 'processing' ? 'Running' : 'Completed'} for {formatElapsedTime()}
          </Typography>
        )}
      </CardContent>

      <style>{`
        .rotating {
          animation: rotate 1s linear infinite;
        }
        
        @keyframes rotate {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </Card>
  );
};

export default ProgressBar;