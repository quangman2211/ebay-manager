import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
import { DataGrid, GridColDef, GridActionsCellItem } from '@mui/x-data-grid';
import { Edit as EditIcon } from '@mui/icons-material';
import { accountsAPI, ordersAPI } from '../services/api';
import type { Account, Order } from '../types';

const Orders: React.FC = () => {
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [selectedAccount, setSelectedAccount] = useState<number | ''>('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(false);
  
  // Status update dialog
  const [statusDialog, setStatusDialog] = useState<{
    open: boolean;
    orderId: number | null;
    currentStatus: string;
  }>({
    open: false,
    orderId: null,
    currentStatus: '',
  });

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
      const ordersData = await ordersAPI.getOrders(
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

  const handleStatusUpdate = async (newStatus: string) => {
    if (!statusDialog.orderId) return;

    try {
      await ordersAPI.updateOrderStatus(statusDialog.orderId, newStatus);
      setStatusDialog({ open: false, orderId: null, currentStatus: '' });
      loadOrders(); // Reload to see updated status
    } catch (error) {
      console.error('Failed to update order status:', error);
    }
  };

  const getStatusColor = (status?: string) => {
    switch (status) {
      case 'pending': return 'warning';
      case 'processing': return 'info';
      case 'shipped': return 'primary';
      case 'completed': return 'success';
      default: return 'default';
    }
  };

  const columns: GridColDef[] = [
    {
      field: 'item_id',
      headerName: 'Order Number',
      width: 150,
      renderCell: (params) => (
        <Typography variant="body2" fontWeight="bold">
          {params.value}
        </Typography>
      ),
    },
    {
      field: 'buyer_name',
      headerName: 'Buyer',
      width: 200,
      valueGetter: (params) => params.row.csv_row['Buyer Name'] || 'N/A',
    },
    {
      field: 'item_title',
      headerName: 'Item',
      width: 300,
      valueGetter: (params) => params.row.csv_row['Item Title'] || 'N/A',
    },
    {
      field: 'sold_for',
      headerName: 'Amount',
      width: 100,
      valueGetter: (params) => params.row.csv_row['Sold For'] || params.row.csv_row['Total Price'] || '$0',
    },
    {
      field: 'sale_date',
      headerName: 'Sale Date',
      width: 120,
      valueGetter: (params) => {
        const date = params.row.csv_row['Sale Date'];
        return date ? new Date(date).toLocaleDateString() : 'N/A';
      },
    },
    {
      field: 'status',
      headerName: 'Status',
      width: 120,
      renderCell: (params) => {
        const status = params.row.order_status?.status || 'pending';
        return (
          <Chip
            label={status.charAt(0).toUpperCase() + status.slice(1)}
            color={getStatusColor(status) as any}
            size="small"
          />
        );
      },
    },
    {
      field: 'actions',
      type: 'actions',
      headerName: 'Actions',
      width: 100,
      getActions: (params) => [
        <GridActionsCellItem
          icon={<EditIcon />}
          label="Update Status"
          onClick={() => {
            setStatusDialog({
              open: true,
              orderId: params.row.id,
              currentStatus: params.row.order_status?.status || 'pending',
            });
          }}
        />,
      ],
    },
  ];

  return (
    <Box>
      <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h4" component="h1">
          Orders
        </Typography>
        
        <Box sx={{ display: 'flex', gap: 2 }}>
          <FormControl sx={{ minWidth: 200 }}>
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

          <FormControl sx={{ minWidth: 150 }}>
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
        columns={columns}
        loading={loading}
        autoHeight
        disableRowSelectionOnClick
        pageSizeOptions={[25, 50, 100]}
        initialState={{
          pagination: { paginationModel: { pageSize: 25 } },
        }}
        sx={{
          '& .MuiDataGrid-cell': {
            borderRight: '1px solid #f0f0f0',
          },
        }}
      />

      {/* Status Update Dialog */}
      <Dialog
        open={statusDialog.open}
        onClose={() => setStatusDialog({ open: false, orderId: null, currentStatus: '' })}
      >
        <DialogTitle>Update Order Status</DialogTitle>
        <DialogContent>
          <FormControl fullWidth sx={{ mt: 2 }}>
            <InputLabel>New Status</InputLabel>
            <Select
              value={statusDialog.currentStatus}
              label="New Status"
              onChange={(e) => setStatusDialog(prev => ({ ...prev, currentStatus: e.target.value }))}
            >
              <MenuItem value="pending">Pending</MenuItem>
              <MenuItem value="processing">Processing</MenuItem>
              <MenuItem value="shipped">Shipped</MenuItem>
              <MenuItem value="completed">Completed</MenuItem>
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setStatusDialog({ open: false, orderId: null, currentStatus: '' })}>
            Cancel
          </Button>
          <Button 
            onClick={() => handleStatusUpdate(statusDialog.currentStatus)}
            variant="contained"
          >
            Update
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Orders;