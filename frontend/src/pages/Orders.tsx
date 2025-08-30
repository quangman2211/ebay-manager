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
import { orderColumns } from '../config/OrderTableColumns';
import { orderStyles } from '../styles/pages/orderStyles';
import { spacing } from '../styles/common/spacing';
import type { Account, Order } from '../types';

const Orders: React.FC = () => {
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [selectedAccount, setSelectedAccount] = useState<number | ''>('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(false);

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
        columns={orderColumns}
        loading={loading}
        autoHeight
        disableRowSelectionOnClick
        pageSizeOptions={[25, 50, 100]}
        initialState={{
          pagination: { paginationModel: { pageSize: 25 } },
        }}
        rowHeight={spacing.rowHeight}
        sx={orderStyles.dataGrid}
      />
    </Box>
  );
};

export default Orders;