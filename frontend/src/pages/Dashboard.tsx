import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip,
} from '@mui/material';
import { useAuth } from '../context/AuthContext';
import { accountsAPI, ordersAPI, listingsAPI } from '../services/api';
import type { Account, Order, Listing } from '../types';

interface DashboardStats {
  totalOrders: number;
  pendingOrders: number;
  shippedOrders: number;
  completedOrders: number;
  totalListings: number;
  activeListings: number;
  todayRevenue: number;
}

const Dashboard: React.FC = () => {
  const { user } = useAuth();
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [selectedAccount, setSelectedAccount] = useState<number | ''>('');
  const [stats, setStats] = useState<DashboardStats>({
    totalOrders: 0,
    pendingOrders: 0,
    shippedOrders: 0,
    completedOrders: 0,
    totalListings: 0,
    activeListings: 0,
    todayRevenue: 0,
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadAccounts();
  }, []);

  useEffect(() => {
    if (selectedAccount) {
      loadStats();
    }
  }, [selectedAccount]);

  const loadAccounts = async () => {
    try {
      const accountsData = await accountsAPI.getAccounts();
      setAccounts(accountsData);
      if (accountsData.length > 0) {
        setSelectedAccount(accountsData[0].id);
      }
    } catch (error) {
      console.error('Failed to load accounts:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadStats = async () => {
    if (!selectedAccount) return;

    try {
      const [orders, listings] = await Promise.all([
        ordersAPI.getOrders(selectedAccount as number),
        listingsAPI.getListings(selectedAccount as number),
      ]);

      // Calculate order stats
      const pendingOrders = orders.filter(o => !o.order_status || o.order_status.status === 'pending').length;
      const processingOrders = orders.filter(o => o.order_status?.status === 'processing').length;
      const shippedOrders = orders.filter(o => o.order_status?.status === 'shipped').length;
      const completedOrders = orders.filter(o => o.order_status?.status === 'completed').length;

      // Calculate revenue (rough estimate from order data)
      const todayRevenue = orders
        .filter(o => {
          if (!o.csv_row['Sale Date']) return false;
          const saleDate = new Date(o.csv_row['Sale Date']);
          const today = new Date();
          return saleDate.toDateString() === today.toDateString();
        })
        .reduce((sum, o) => {
          const price = o.csv_row['Total Price'] || o.csv_row['Sold For'] || '$0';
          const numPrice = parseFloat(price.replace('$', '').replace(',', ''));
          return sum + (isNaN(numPrice) ? 0 : numPrice);
        }, 0);

      // Calculate listing stats
      const activeListings = listings.filter(l => {
        const quantity = l.csv_row['Available quantity'];
        return quantity && parseInt(quantity) > 0;
      }).length;

      setStats({
        totalOrders: orders.length,
        pendingOrders: pendingOrders + processingOrders,
        shippedOrders,
        completedOrders,
        totalListings: listings.length,
        activeListings,
        todayRevenue,
      });
    } catch (error) {
      console.error('Failed to load stats:', error);
    }
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
        <Typography>Loading...</Typography>
      </Box>
    );
  }

  return (
    <Box>
      <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h4" component="h1">
          Dashboard
        </Typography>
        
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
      </Box>

      <Grid container spacing={3}>
        {/* Order Stats */}
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Total Orders
              </Typography>
              <Typography variant="h4">
                {stats.totalOrders}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Pending Orders
              </Typography>
              <Typography variant="h4">
                {stats.pendingOrders}
              </Typography>
              <Chip 
                label={stats.pendingOrders > 0 ? 'Action Needed' : 'Up to Date'}
                color={stats.pendingOrders > 0 ? 'warning' : 'success'}
                size="small"
                sx={{ mt: 1 }}
              />
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Shipped Orders
              </Typography>
              <Typography variant="h4">
                {stats.shippedOrders}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Completed Orders
              </Typography>
              <Typography variant="h4">
                {stats.completedOrders}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Listing Stats */}
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Total Listings
              </Typography>
              <Typography variant="h4">
                {stats.totalListings}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Active Listings
              </Typography>
              <Typography variant="h4">
                {stats.activeListings}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Today's Revenue
              </Typography>
              <Typography variant="h4">
                ${stats.todayRevenue.toFixed(2)}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Account Status
              </Typography>
              <Typography variant="h6">
                {user?.role === 'admin' ? 'Admin Access' : 'Staff Access'}
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Managing {accounts.length} account(s)
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard;