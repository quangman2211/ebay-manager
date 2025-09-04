import React, { useState, useEffect, useMemo } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Chip,
} from '@mui/material';
import { useAuth } from '../context/AuthContext';
import { useAccount } from '../context/AccountContext';
import { useAccountManagement } from '../hooks/useAccountManagement';
import { ordersAPI, listingsAPI } from '../services/api';
import { dashboardStyles } from '../styles/pages/dashboardStyles';
import { useResponsive } from '../hooks/useResponsive';
import type { Order, Listing } from '../types';

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
  const { state: accountState } = useAccount();
  const { accounts } = useAccountManagement();
  const { isMini, isMobile, isTablet, breakpoint } = useResponsive();
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

  // Memoize grid configuration based on screen size including mini mode
  const gridConfig = useMemo(() => {
    if (isMini) return dashboardStyles.gridItemConfig.mini;
    if (isMobile) return dashboardStyles.gridItemConfig.mobile;
    if (isTablet) return dashboardStyles.gridItemConfig.medium;
    return dashboardStyles.gridItemConfig.large;
  }, [isMini, isMobile, isTablet]);

  // Memoize responsive spacing based on breakpoint including mini mode
  const responsiveSpacing = useMemo(() => {
    return dashboardStyles.gridContainer.spacing[breakpoint] || dashboardStyles.gridContainer.spacing.md;
  }, [breakpoint]);

  useEffect(() => {
    // Load stats for both "All Accounts" (null) and specific accounts
    loadStats();
  }, [accountState.currentAccount]);

  const loadStats = async () => {
    setLoading(true);
    try {
      // If currentAccount is null, get data from all accounts
      // If currentAccount is set, get data from specific account
      const accountId = accountState.currentAccount?.id;
      const [orders, listings] = await Promise.all([
        ordersAPI.getOrders(accountId),
        listingsAPI.getListings(accountId),
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
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Box sx={dashboardStyles.loadingContainer}>
        <Typography>Loading...</Typography>
      </Box>
    );
  }

  return (
    <Box sx={{
      ...dashboardStyles.dashboardContainer,
      ...(isMini && {
        // Mini mode optimizations
        display: 'flex',
        flexDirection: 'column',
        height: '100%'
      })
    }}>
      <Box sx={dashboardStyles.headerContainer}>
        <Typography 
          variant="h4" 
          component="h1"
          sx={dashboardStyles.pageTitle}
        >
          Dashboard
        </Typography>
      </Box>

      <Box sx={{
        ...(isMini && {
          flex: 1
        })
      }}>
        <Grid container spacing={responsiveSpacing} sx={dashboardStyles.gridContainer}>
        {/* Order Stats */}
        <Grid item {...gridConfig}>
          <Card sx={dashboardStyles.metricCard}>
            <CardContent sx={dashboardStyles.cardContent}>
              <Typography sx={dashboardStyles.metricLabel}>
                Total Orders
              </Typography>
              <Typography sx={dashboardStyles.metricValue}>
                {stats.totalOrders}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item {...gridConfig}>
          <Card sx={dashboardStyles.metricCard}>
            <CardContent sx={dashboardStyles.cardContent}>
              <Typography sx={dashboardStyles.metricLabel}>
                Pending Orders
              </Typography>
              <Typography sx={dashboardStyles.metricValue}>
                {stats.pendingOrders}
              </Typography>
              <Chip 
                label={stats.pendingOrders > 0 ? 'Action Needed' : 'Up to Date'}
                color={stats.pendingOrders > 0 ? 'warning' : 'success'}
                size="small"
                sx={dashboardStyles.statusChip}
              />
            </CardContent>
          </Card>
        </Grid>

        <Grid item {...gridConfig}>
          <Card sx={dashboardStyles.metricCard}>
            <CardContent sx={dashboardStyles.cardContent}>
              <Typography sx={dashboardStyles.metricLabel}>
                Shipped Orders
              </Typography>
              <Typography sx={dashboardStyles.metricValue}>
                {stats.shippedOrders}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item {...gridConfig}>
          <Card sx={dashboardStyles.metricCard}>
            <CardContent sx={dashboardStyles.cardContent}>
              <Typography sx={dashboardStyles.metricLabel}>
                Completed Orders
              </Typography>
              <Typography sx={dashboardStyles.metricValue}>
                {stats.completedOrders}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Listing Stats */}
        <Grid item {...gridConfig}>
          <Card sx={dashboardStyles.metricCard}>
            <CardContent sx={dashboardStyles.cardContent}>
              <Typography sx={dashboardStyles.metricLabel}>
                Total Listings
              </Typography>
              <Typography sx={dashboardStyles.metricValue}>
                {stats.totalListings}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item {...gridConfig}>
          <Card sx={dashboardStyles.metricCard}>
            <CardContent sx={dashboardStyles.cardContent}>
              <Typography sx={dashboardStyles.metricLabel}>
                Active Listings
              </Typography>
              <Typography sx={dashboardStyles.metricValue}>
                {stats.activeListings}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item {...gridConfig}>
          <Card sx={dashboardStyles.metricCard}>
            <CardContent sx={dashboardStyles.cardContent}>
              <Typography sx={dashboardStyles.metricLabel}>
                Today's Revenue
              </Typography>
              <Typography sx={dashboardStyles.metricValue}>
                ${stats.todayRevenue.toFixed(2)}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item {...gridConfig}>
          <Card sx={dashboardStyles.metricCard}>
            <CardContent sx={dashboardStyles.cardContent}>
              <Typography sx={dashboardStyles.metricLabel}>
                Account Status
              </Typography>
              <Typography variant="h6" sx={{ 
                fontSize: {
                  mini: '0.875rem',   // Smaller on mini screens
                  xs: '1rem',
                  sm: '1.125rem', 
                  md: '1.25rem'
                },
                fontWeight: 600,
                mb: {
                  mini: 0.5,          // Less margin on mini screens
                  xs: 1
                }
              }}>
                {isMini ? (user?.role === 'admin' ? 'Admin' : 'Staff') : (user?.role === 'admin' ? 'Admin Access' : 'Staff Access')}
              </Typography>
              <Typography variant="body2" sx={{
                color: 'text.secondary',
                fontSize: {
                  mini: '0.625rem',   // Smaller on mini screens
                  xs: '0.75rem',
                  sm: '0.875rem'
                }
              }}>
                {isMini ? `${accounts.length} account(s)` : `Managing ${accounts.length} account(s)`}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        </Grid>
      </Box>
    </Box>
  );
};

export default Dashboard;