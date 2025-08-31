import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
} from '@mui/material';
import { DataGrid } from '@mui/x-data-grid';
import { accountsAPI } from '../services/api';
import OrderDataService from '../services/OrderDataService';
import { createOrderColumns } from '../config/OrderTableColumns';
import { orderStyles } from '../styles/pages/orderStyles';
import { spacing } from '../styles/common/spacing';
import OrderDetailModal from '../components/orders/OrderDetailModal';
import type { Account, Order, OrderNote } from '../types';

const Orders: React.FC = () => {
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [selectedAccount, setSelectedAccount] = useState<number | ''>('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedOrder, setSelectedOrder] = useState<Order | null>(null);
  const [modalOpen, setModalOpen] = useState(false);

  useEffect(() => {
    loadAccounts();
  }, []);

  useEffect(() => {
    if (selectedAccount) {
      loadOrders();
    }
  }, [selectedAccount, statusFilter]);

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

  const loadOrders = async () => {
    if (!selectedAccount) return;
    
    setLoading(true);
    try {
      const ordersData = await OrderDataService.fetchOrders(
        selectedAccount as number,
        statusFilter || undefined
      );
      setOrders(ordersData);
    } catch (error) {
      console.error('Failed to load orders:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleRowClick = (params: any) => {
    setSelectedOrder(params.row);
    setModalOpen(true);
  };

  const handleCloseModal = () => {
    setModalOpen(false);
    setSelectedOrder(null);
  };

  const handleStatusUpdate = (orderId: number, newStatus: string) => {
    setOrders(prevOrders => 
      prevOrders.map(order => 
        order.id === orderId 
          ? {
              ...order,
              order_status: {
                ...order.order_status,
                id: order.order_status?.id || 0,
                csv_data_id: order.id,
                status: newStatus as any,
                updated_by: 1,
                updated_at: new Date().toISOString(),
              }
            }
          : order
      )
    );
  };

  const handleTrackingUpdate = (orderId: number, trackingNumber: string) => {
    setOrders(prevOrders => 
      prevOrders.map(order => 
        order.id === orderId 
          ? {
              ...order,
              csv_row: {
                ...order.csv_row,
                'Tracking Number': trackingNumber,
              }
            }
          : order
      )
    );
  };

  const handleNotesUpdate = (orderId: number, notes: OrderNote[]) => {
    setOrders(prevOrders => 
      prevOrders.map(order => 
        order.id === orderId 
          ? { ...order, notes }
          : order
      )
    );
    
    if (selectedOrder && selectedOrder.id === orderId) {
      setSelectedOrder({ ...selectedOrder, notes });
    }
  };

  return (
    <Box>
      <Box sx={orderStyles.headerContainer}>
        <Typography variant="h4" component="h1">
          Orders
        </Typography>
        
        <Box sx={orderStyles.filtersContainer}>
          <FormControl sx={orderStyles.accountSelect}>
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

      <DataGrid
        rows={orders}
        columns={createOrderColumns(handleStatusUpdate, handleTrackingUpdate)}
        loading={loading}
        autoHeight
        disableRowSelectionOnClick
        pageSizeOptions={[25, 50, 100]}
        initialState={{
          pagination: { paginationModel: { pageSize: 25 } },
        }}
        rowHeight={spacing.rowHeight}
        sx={{
          ...orderStyles.dataGrid,
          '& .MuiDataGrid-row': {
            cursor: 'pointer',
            '&:hover': {
              backgroundColor: 'rgba(0, 0, 0, 0.04)',
            },
          },
        }}
        onRowClick={handleRowClick}
      />

      <OrderDetailModal
        order={selectedOrder}
        open={modalOpen}
        onClose={handleCloseModal}
        onNotesUpdate={handleNotesUpdate}
      />
    </Box>
  );
};

export default Orders;