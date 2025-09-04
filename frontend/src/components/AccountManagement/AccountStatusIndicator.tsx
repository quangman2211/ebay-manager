import React from 'react';
import {
  Box,
  Chip,
  Tooltip,
  Typography,
} from '@mui/material';
import {
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  Schedule as ScheduleIcon,
  Sync as SyncIcon,
  SyncDisabled as SyncDisabledIcon,
} from '@mui/icons-material';
import { Account } from '../../types';

type ConnectionStatus = 'authenticated' | 'pending' | 'expired' | 'failed';

interface AccountStatusIndicatorProps {
  account: Account;
  variant?: 'chip' | 'detailed' | 'compact';
  showSync?: boolean;
}

/**
 * Account Status Indicator Component
 * Follows Single Responsibility Principle - displays account status information
 * Open/Closed Principle - extensible for new status types
 */
const AccountStatusIndicator: React.FC<AccountStatusIndicatorProps> = ({
  account,
  variant = 'chip',
  showSync = true,
}) => {
  const getConnectionStatusProps = (status: ConnectionStatus | undefined) => {
    switch (status) {
      case 'authenticated':
        return {
          color: 'success' as const,
          icon: <CheckCircleIcon />,
          label: 'Connected',
          description: 'Account is authenticated and connected',
        };
      case 'pending':
        return {
          color: 'warning' as const,
          icon: <ScheduleIcon />,
          label: 'Pending',
          description: 'Connection authentication pending',
        };
      case 'expired':
        return {
          color: 'error' as const,
          icon: <WarningIcon />,
          label: 'Expired',
          description: 'Connection credentials have expired',
        };
      case 'failed':
        return {
          color: 'error' as const,
          icon: <ErrorIcon />,
          label: 'Failed',
          description: 'Connection authentication failed',
        };
      default:
        return {
          color: 'default' as const,
          icon: <WarningIcon />,
          label: 'Unknown',
          description: 'Connection status unknown',
        };
    }
  };

  const getDataProcessingStatusProps = (processingEnabled: boolean | undefined) => {
    return processingEnabled
      ? {
          color: 'success' as const,
          icon: <SyncIcon />,
          label: 'Processing Enabled',
          description: 'CSV data processing is enabled',
        }
      : {
          color: 'default' as const,
          icon: <SyncDisabledIcon />,
          label: 'Processing Disabled', 
          description: 'CSV data processing is disabled',
        };
  };

  const getActiveStatusProps = (isActive: boolean) => {
    return isActive
      ? {
          color: 'success' as const,
          label: 'Active',
          description: 'Account is active and operational',
        }
      : {
          color: 'error' as const,
          label: 'Inactive',
          description: 'Account is deactivated',
        };
  };

  const connectionStatus = getConnectionStatusProps(account.connection_status);
  const processingStatus = getDataProcessingStatusProps(account.data_processing_enabled);
  const activeStatus = getActiveStatusProps(account.is_active);

  if (variant === 'chip') {
    return (
      <Box sx={{ display: 'flex', gap: 0.5, alignItems: 'center' }}>
        <Tooltip title={connectionStatus.description}>
          <Chip
            icon={connectionStatus.icon}
            label={connectionStatus.label}
            size="small"
            color={connectionStatus.color}
          />
        </Tooltip>
        
        <Tooltip title={activeStatus.description}>
          <Chip
            label={activeStatus.label}
            size="small"
            color={activeStatus.color}
            variant="outlined"
          />
        </Tooltip>

        {showSync && (
          <Tooltip title={processingStatus.description}>
            <Chip
              icon={processingStatus.icon}
              label={processingStatus.label}
              size="small"
              color={processingStatus.color}
              variant="outlined"
            />
          </Tooltip>
        )}
      </Box>
    );
  }

  if (variant === 'compact') {
    return (
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <Tooltip title={`Connection: ${connectionStatus.description}`}>
          <Box sx={{ display: 'flex', alignItems: 'center', color: `${connectionStatus.color}.main` }}>
            {connectionStatus.icon}
          </Box>
        </Tooltip>
        
        {showSync && (
          <Tooltip title={`Processing: ${processingStatus.description}`}>
            <Box sx={{ display: 'flex', alignItems: 'center', color: `${processingStatus.color}.main` }}>
              {processingStatus.icon}
            </Box>
          </Tooltip>
        )}
        
        <Typography variant="caption" color="text.secondary">
          {activeStatus.label}
        </Typography>
      </Box>
    );
  }

  // Detailed variant
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        {connectionStatus.icon}
        <Typography variant="body2">
          Connection: <strong>{connectionStatus.label}</strong>
        </Typography>
      </Box>
      
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <CheckCircleIcon color={activeStatus.color} />
        <Typography variant="body2">
          Account Status: <strong>{activeStatus.label}</strong>
        </Typography>
      </Box>

      {showSync && (
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          {processingStatus.icon}
          <Typography variant="body2">
            Data Processing: <strong>{processingStatus.label}</strong>
          </Typography>
        </Box>
      )}

      {account.last_sync_at && (
        <Typography variant="caption" color="text.secondary">
          Last synced: {new Date(account.last_sync_at).toLocaleString()}
        </Typography>
      )}
      
      {account.platform_username && (
        <Typography variant="caption" color="text.secondary">
          Platform ID: {account.platform_username}
        </Typography>
      )}
    </Box>
  );
};

export default AccountStatusIndicator;