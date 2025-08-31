import React, { useState } from 'react';
import {
  Box,
  Select,
  MenuItem,
  FormControl,
  Chip,
  IconButton,
  CircularProgress,
  Snackbar,
  Alert,
} from '@mui/material';
import { Edit, Save, Cancel } from '@mui/icons-material';
import OrderDataService from '../../services/OrderDataService';
import { colors } from '../../styles/common/colors';
import { spacing } from '../../styles/common/spacing';
import type { Order } from '../../types';

interface OrderStatusEditorProps {
  order: Order;
  onStatusUpdate: (orderId: number, newStatus: string) => void;
}

type OrderStatus = 'pending' | 'processing' | 'shipped' | 'completed';

interface IStatusValidator {
  isValidTransition(from: string, to: string): boolean;
  getValidTransitions(from: string): OrderStatus[];
}

class StatusValidator implements IStatusValidator {
  private validTransitions: Record<string, OrderStatus[]> = {
    pending: ['processing', 'cancelled'],
    processing: ['shipped', 'cancelled'],
    shipped: ['completed'],
    completed: [],
    cancelled: [],
  };

  isValidTransition(from: string, to: string): boolean {
    return this.validTransitions[from]?.includes(to as OrderStatus) || false;
  }

  getValidTransitions(from: string): OrderStatus[] {
    return this.validTransitions[from] || [];
  }
}

const statusValidator = new StatusValidator();

const OrderStatusEditor: React.FC<OrderStatusEditorProps> = ({ order, onStatusUpdate }) => {
  const currentStatus = order.order_status?.status || 'pending';
  const [isEditing, setIsEditing] = useState(false);
  const [selectedStatus, setSelectedStatus] = useState(currentStatus);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending': return colors.warning;
      case 'processing': return colors.info;
      case 'shipped': return colors.secondary;
      case 'completed': return colors.success;
      case 'cancelled': return colors.error;
      default: return colors.text.secondary;
    }
  };

  const handleEditClick = () => {
    setIsEditing(true);
    setSelectedStatus(currentStatus);
  };

  const handleCancelEdit = () => {
    setIsEditing(false);
    setSelectedStatus(currentStatus);
    setError(null);
  };

  const handleSaveStatus = async () => {
    if (selectedStatus === currentStatus) {
      setIsEditing(false);
      return;
    }

    if (!statusValidator.isValidTransition(currentStatus, selectedStatus)) {
      setError(`Invalid status transition from ${currentStatus} to ${selectedStatus}`);
      return;
    }

    setLoading(true);
    try {
      await OrderDataService.updateOrderStatus(order.id, selectedStatus);
      onStatusUpdate(order.id, selectedStatus);
      setIsEditing(false);
      setError(null);
    } catch (error) {
      console.error('Failed to update order status:', error);
      setError('Failed to update order status. Please try again.');
      setSelectedStatus(currentStatus);
    } finally {
      setLoading(false);
    }
  };

  if (isEditing) {
    const validTransitions = statusValidator.getValidTransitions(currentStatus);
    const allStatuses: OrderStatus[] = ['pending', 'processing', 'shipped', 'completed'];
    const availableStatuses = allStatuses.filter(status => 
      status === currentStatus || validTransitions.includes(status)
    );

    return (
      <Box sx={{ display: 'flex', alignItems: 'center', gap: spacing.small }}>
        <FormControl size="small" sx={{ minWidth: 120 }}>
          <Select
            value={selectedStatus}
            onChange={(e) => setSelectedStatus(e.target.value)}
            disabled={loading}
          >
            {availableStatuses.map((status) => (
              <MenuItem key={status} value={status}>
                {status.charAt(0).toUpperCase() + status.slice(1)}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
        
        <IconButton 
          size="small" 
          onClick={handleSaveStatus}
          disabled={loading}
          sx={{ color: colors.success }}
        >
          {loading ? <CircularProgress size={16} /> : <Save />}
        </IconButton>
        
        <IconButton 
          size="small" 
          onClick={handleCancelEdit}
          disabled={loading}
          sx={{ color: colors.error }}
        >
          <Cancel />
        </IconButton>

        <Snackbar 
          open={!!error} 
          autoHideDuration={6000} 
          onClose={() => setError(null)}
        >
          <Alert severity="error" onClose={() => setError(null)}>
            {error}
          </Alert>
        </Snackbar>
      </Box>
    );
  }

  return (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: spacing.small }}>
      <Chip
        label={currentStatus.charAt(0).toUpperCase() + currentStatus.slice(1)}
        sx={{
          backgroundColor: getStatusColor(currentStatus),
          color: colors.background.paper,
          fontWeight: 600,
        }}
      />
      <IconButton 
        size="small" 
        onClick={handleEditClick}
        sx={{ color: colors.text.secondary }}
      >
        <Edit />
      </IconButton>
    </Box>
  );
};

export default OrderStatusEditor;