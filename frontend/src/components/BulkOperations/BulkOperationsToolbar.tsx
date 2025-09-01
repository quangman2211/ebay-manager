import React, { useState, useMemo } from 'react';
import {
  Box,
  Typography,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  LinearProgress,
  Chip,
  List,
  ListItem,
  ListItemText,
  IconButton,
  Collapse,
  Alert,
} from '@mui/material';
import {
  PlayArrow as PlayArrowIcon,
  Clear as ClearIcon,
  Cancel as CancelIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
} from '@mui/icons-material';
import type { Order, BulkOperationResult } from '../../types';

export interface BulkOperationsToolbarProps {
  selectedOrders: Order[];
  onBulkUpdate: (orderIds: number[], status: string) => void;
  onClearSelection: () => void;
  loading: boolean;
  progress?: number;
  onCancel?: () => void;
  lastResult?: BulkOperationResult;
}

const statusTransitions: Record<string, string[]> = {
  pending: ['processing', 'shipped'],
  processing: ['shipped', 'completed'],
  shipped: ['completed'],
  completed: [],
};

const BulkOperationsToolbar: React.FC<BulkOperationsToolbarProps> = ({
  selectedOrders,
  onBulkUpdate,
  onClearSelection,
  loading,
  progress,
  onCancel,
  lastResult,
}) => {
  const [selectedStatus, setSelectedStatus] = useState('');
  const [showConfirmDialog, setShowConfirmDialog] = useState(false);
  const [showErrorDetails, setShowErrorDetails] = useState(false);

  const hasSelection = selectedOrders.length > 0;
  const orderIds = useMemo(() => selectedOrders.map(order => order.id), [selectedOrders]);

  // Determine valid status transitions based on selected orders
  const validStatuses = useMemo(() => {
    if (selectedOrders.length === 0) return [];
    
    // Get all unique current statuses
    const currentStatuses = Array.from(new Set(
      selectedOrders.map(order => order.order_status?.status || 'pending')
    ));
    
    // If all orders have the same status, show only valid transitions for that status
    if (currentStatuses.length === 1) {
      return statusTransitions[currentStatuses[0]] || [];
    }
    
    // If orders have mixed statuses, show all possible statuses
    // This allows flexible bulk updates to any status for mixed selections  
    const allStatuses = ['pending', 'processing', 'shipped', 'completed'];
    return allStatuses;
  }, [selectedOrders]);

  const handleUpdateClick = () => {
    if (selectedStatus && hasSelection) {
      setShowConfirmDialog(true);
    }
  };

  const handleConfirmUpdate = () => {
    onBulkUpdate(orderIds, selectedStatus);
    setShowConfirmDialog(false);
    setSelectedStatus('');
  };

  const handleCancelConfirm = () => {
    setShowConfirmDialog(false);
  };

  const getStatusLabel = (status: string): string => {
    return status.charAt(0).toUpperCase() + status.slice(1);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending': return 'warning';
      case 'processing': return 'info';
      case 'shipped': return 'secondary';
      case 'completed': return 'success';
      default: return 'default';
    }
  };

  const renderResultSummary = () => {
    if (!lastResult) return null;

    const { successful, failed, errors } = lastResult;
    
    return (
      <Box sx={{ mb: 2 }}>
        <Alert 
          severity={failed.length === 0 ? 'success' : 'warning'}
          sx={{ mb: 1 }}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Typography variant="body2">
              {successful.length} updated successfully
              {failed.length > 0 && `, ${failed.length} failed`}
            </Typography>
            {failed.length > 0 && (
              <Button
                size="small"
                onClick={() => setShowErrorDetails(!showErrorDetails)}
                endIcon={showErrorDetails ? <ExpandLessIcon /> : <ExpandMoreIcon />}
              >
                View Errors
              </Button>
            )}
          </Box>
        </Alert>
        
        <Collapse in={showErrorDetails}>
          <Alert data-testid="error-details" severity="error" sx={{ mt: 1 }}>
            <Typography variant="subtitle2" gutterBottom>
              Error Details:
            </Typography>
            <List dense>
              {errors.map((error, index) => (
                <ListItem key={index} sx={{ py: 0 }}>
                  <ListItemText 
                    primary={error}
                    primaryTypographyProps={{ variant: 'body2' }}
                  />
                </ListItem>
              ))}
            </List>
          </Alert>
        </Collapse>
      </Box>
    );
  };

  if (loading) {
    return (
      <Box 
        data-testid="progress-dialog"
        sx={{ 
          p: 2, 
          bgcolor: 'background.paper', 
          borderRadius: 1, 
          mb: 2,
          border: '1px solid',
          borderColor: 'divider',
        }}
        role="region"
        aria-label="Bulk operations progress"
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
          <Typography variant="h6">Processing Bulk Operation</Typography>
          {onCancel && (
            <Button
              variant="outlined"
              color="error"
              size="small"
              startIcon={<CancelIcon />}
              onClick={onCancel}
            >
              Cancel
            </Button>
          )}
        </Box>
        
        <LinearProgress 
          variant={progress !== undefined ? 'determinate' : 'indeterminate'}
          value={progress}
          sx={{ mb: 1 }}
          role="progressbar"
          aria-valuenow={progress}
          aria-valuemin={0}
          aria-valuemax={100}
        />
        
        <Typography variant="body2" color="text.secondary">
          {progress !== undefined ? `${progress}% complete` : 'Processing...'}
        </Typography>
      </Box>
    );
  }

  return (
    <Box
      data-testid="bulk-operations-toolbar"
      sx={{
        p: 2,
        bgcolor: 'background.paper',
        borderRadius: 1,
        mb: 2,
        border: '1px solid',
        borderColor: hasSelection ? 'primary.main' : 'divider',
      }}
      role="region"
      aria-label="Bulk operations toolbar"
    >
      {renderResultSummary()}
      
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
        <Typography variant="h6">Bulk Actions</Typography>
        <Chip
          data-testid="selected-count"
          label={`${selectedOrders.length} order${selectedOrders.length === 1 ? '' : 's'} selected`}
          color={hasSelection ? 'primary' : 'default'}
          size="small"
        />
      </Box>

      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
        <FormControl size="small" sx={{ minWidth: 140 }}>
          <InputLabel id="bulk-status-label">New Status</InputLabel>
          <Select
            data-testid="status-select"
            labelId="bulk-status-label"
            value={selectedStatus}
            label="New Status"
            onChange={(e) => setSelectedStatus(e.target.value)}
            disabled={!hasSelection}
          >
            {validStatuses.map((status) => (
              <MenuItem key={status} value={status} data-testid={`status-option-${status}`}>
                {getStatusLabel(status)}
              </MenuItem>
            ))}
          </Select>
        </FormControl>

        <Button
          data-testid="bulk-status-update-btn"
          variant="contained"
          startIcon={<PlayArrowIcon />}
          onClick={handleUpdateClick}
          disabled={!hasSelection || !selectedStatus}
          aria-label="Update status for selected orders"
        >
          Update Status
        </Button>

        <Button
          variant="outlined"
          startIcon={<ClearIcon />}
          onClick={onClearSelection}
          disabled={!hasSelection}
          aria-label="Clear selection"
        >
          Clear Selection
        </Button>
      </Box>

      {/* Confirmation Dialog */}
      <Dialog
        data-testid="confirmation-dialog"
        open={showConfirmDialog}
        onClose={handleCancelConfirm}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Confirm Bulk Update</DialogTitle>
        <DialogContent>
          <Typography gutterBottom>
            Are you sure you want to update {selectedOrders.length} orders to "{getStatusLabel(selectedStatus)}"?
          </Typography>
          
          <Typography variant="subtitle2" sx={{ mt: 2, mb: 1 }}>
            Affected Orders:
          </Typography>
          <List dense sx={{ maxHeight: 200, overflow: 'auto' }}>
            {selectedOrders.slice(0, 10).map((order) => (
              <ListItem key={order.id}>
                <ListItemText
                  primary={order.csv_row['Order Number'] || order.item_id}
                  secondary={
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Chip
                        label={getStatusLabel(order.order_status?.status || 'pending')}
                        color={getStatusColor(order.order_status?.status || 'pending') as any}
                        size="small"
                      />
                      <Typography variant="caption">
                        → {getStatusLabel(selectedStatus)}
                      </Typography>
                    </Box>
                  }
                />
              </ListItem>
            ))}
            {selectedOrders.length > 10 && (
              <ListItem>
                <ListItemText
                  primary={`... and ${selectedOrders.length - 10} more orders`}
                  primaryTypographyProps={{ style: { fontStyle: 'italic' } }}
                />
              </ListItem>
            )}
          </List>
        </DialogContent>
        <DialogActions>
          <Button data-testid="cancel-bulk-operation" onClick={handleCancelConfirm}>Cancel</Button>
          <Button 
            data-testid="confirm-bulk-operation"
            onClick={handleConfirmUpdate} 
            variant="contained"
            color="primary"
            autoFocus
          >
            Confirm
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default BulkOperationsToolbar;