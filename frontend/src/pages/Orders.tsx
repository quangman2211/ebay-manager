import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Typography,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  Snackbar,
} from '@mui/material';
import { DataGrid, GridRowSelectionModel } from '@mui/x-data-grid';
import { useAccount } from '../context/AccountContext';
import OrderDataService from '../services/OrderDataService';
import { orderColumns } from '../config/OrderTableColumns';
import { orderStyles } from '../styles/pages/orderStyles';
import { spacing } from '../styles/common/spacing';
import { useBulkSelection } from '../hooks/useBulkSelection';
import BulkOperationsToolbar from '../components/BulkOperations/BulkOperationsToolbar';
import type { Order, BulkOperationResult } from '../types';

const Orders: React.FC = () => {
  const { state: accountState } = useAccount();
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(false);
  const [bulkLoading, setBulkLoading] = useState(false);
  const [bulkProgress, setBulkProgress] = useState<number | undefined>();
  const [bulkResult, setBulkResult] = useState<BulkOperationResult | undefined>();
  const [notification, setNotification] = useState<{
    open: boolean;
    message: string;
    severity: 'success' | 'error' | 'warning';
  }>({ open: false, message: '', severity: 'success' });

  // Initialize bulk selection hook
  const bulkSelection = useBulkSelection(orders, {
    maxSelection: 100,
    onSelectionLimitReached: (limit) => {
      setNotification({
        open: true,
        message: `Maximum ${limit} orders can be selected at once`,
        severity: 'warning',
      });
    },
  });

  useEffect(() => {
    // Load orders for both "All Accounts" (null) and specific accounts
    loadOrders();
  }, [accountState.currentAccount, statusFilter]);

  const loadOrders = async () => {
    setLoading(true);
    try {
      // If currentAccount is null, get orders from all accounts
      // If currentAccount is set, get orders from specific account
      const accountId = accountState.currentAccount?.id;
      const ordersData = await OrderDataService.fetchOrders(
        accountId,
        statusFilter || undefined
      );
      setOrders(ordersData);
      // Clear previous bulk result when loading new data
      setBulkResult(undefined);
    } catch (error) {
      console.error('Failed to load orders:', error);
      setNotification({
        open: true,
        message: 'Failed to load orders',
        severity: 'error',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleBulkUpdate = useCallback(async (orderIds: number[], status: string) => {
    setBulkLoading(true);
    setBulkProgress(0);
    setBulkResult(undefined);

    try {
      // Simulate progress updates
      const progressInterval = setInterval(() => {
        setBulkProgress(prev => {
          if (prev === undefined) return 10;
          return Math.min(prev + 20, 90);
        });
      }, 500);

      const result = await OrderDataService.bulkUpdateOrderStatus(orderIds, status);
      
      clearInterval(progressInterval);
      setBulkProgress(100);
      setBulkResult(result);

      // Show notification
      const { successful, failed } = result;
      if (failed.length === 0) {
        setNotification({
          open: true,
          message: `Successfully updated ${successful.length} orders`,
          severity: 'success',
        });
      } else {
        setNotification({
          open: true,
          message: `Updated ${successful.length} orders, ${failed.length} failed`,
          severity: 'warning',
        });
      }

      // Clear selection and reload orders
      bulkSelection.clearSelection();
      await loadOrders();

    } catch (error) {
      console.error('Bulk update failed:', error);
      setNotification({
        open: true,
        message: 'Bulk update failed. Please try again.',
        severity: 'error',
      });
    } finally {
      setBulkLoading(false);
      setBulkProgress(undefined);
    }
  }, [bulkSelection, loadOrders]);

  const handleCloseNotification = () => {
    setNotification(prev => ({ ...prev, open: false }));
  };

  const handleRowSelectionModelChange = (newSelectionModel: GridRowSelectionModel) => {
    // Sync DataGrid selection with bulk selection hook
    const selectedIds = newSelectionModel as number[];
    const currentIds = bulkSelection.selectedOrderIds;
    
    // Determine if this is a select-all operation
    const isSelectAll = selectedIds.length === orders.length && currentIds.length === 0;
    const isClearAll = selectedIds.length === 0 && currentIds.length === orders.length;
    
    if (isSelectAll) {
      // Use the optimized selectAll method for select-all operations
      bulkSelection.selectAll();
    } else if (isClearAll) {
      // Use the optimized clearSelection for clear-all operations
      bulkSelection.clearSelection();
    } else {
      // For individual selections, find the difference and update accordingly
      const added = selectedIds.filter(id => !currentIds.includes(id));
      const removed = currentIds.filter(id => !selectedIds.includes(id));
      
      // Process removals first, then additions
      removed.forEach(id => bulkSelection.toggleOrder(id));
      added.forEach(id => bulkSelection.toggleOrder(id));
    }
  };

  return (
    <Box>
      <Box sx={orderStyles.headerContainer}>
        <Typography variant="h4" component="h1">
          Orders
        </Typography>
        
        <Box sx={orderStyles.filtersContainer}>
          <FormControl sx={orderStyles.statusSelect}>
            <InputLabel>Status Filter</InputLabel>
            <Select
              value={statusFilter}
              label="Status Filter"
              onChange={(e) => setStatusFilter(e.target.value)}
            >
              <MenuItem value="">All</MenuItem>
              <MenuItem value="pending">Pending</MenuItem>
              <MenuItem value="processing">Processing</MenuItem>
              <MenuItem value="shipped">Shipped</MenuItem>
              <MenuItem value="completed">Completed</MenuItem>
            </Select>
          </FormControl>
        </Box>
      </Box>

      {/* Bulk Operations Toolbar */}
      <BulkOperationsToolbar
        selectedOrders={bulkSelection.selectedOrders}
        onBulkUpdate={handleBulkUpdate}
        onClearSelection={bulkSelection.clearSelection}
        loading={bulkLoading}
        progress={bulkProgress}
        lastResult={bulkResult}
      />

      <DataGrid
        data-testid="orders-datagrid"
        rows={orders}
        columns={orderColumns}
        loading={loading}
        autoHeight
        checkboxSelection
        disableRowSelectionOnClick
        rowSelectionModel={bulkSelection.selectedOrderIds}
        onRowSelectionModelChange={handleRowSelectionModelChange}
        pageSizeOptions={[25, 50, 100]}
        initialState={{
          pagination: { paginationModel: { pageSize: 25 } },
        }}
        rowHeight={spacing.rowHeight}
        sx={orderStyles.dataGrid}
      />

      {/* Notification Snackbar */}
      <Snackbar
        open={notification.open}
        autoHideDuration={6000}
        onClose={handleCloseNotification}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert 
          onClose={handleCloseNotification} 
          severity={notification.severity}
          variant="filled"
        >
          {notification.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default Orders;