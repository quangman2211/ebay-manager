import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  TextField,
  Chip,
} from '@mui/material';
import { DataGrid, GridColDef } from '@mui/x-data-grid';
import { useAccount } from '../context/AccountContext';
import { listingsAPI } from '../services/api';
import type { Listing } from '../types';

const Listings: React.FC = () => {
  const { state: accountState } = useAccount();
  const [searchText, setSearchText] = useState('');
  const [listings, setListings] = useState<Listing[]>([]);
  const [filteredListings, setFilteredListings] = useState<Listing[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // Load listings for both "All Accounts" (null) and specific accounts
    loadListings();
  }, [accountState.currentAccount]);

  useEffect(() => {
    // Filter listings based on search text
    if (!searchText.trim()) {
      setFilteredListings(listings);
    } else {
      const filtered = listings.filter(listing => 
        listing.csv_row['Title']?.toLowerCase().includes(searchText.toLowerCase()) ||
        listing.item_id?.toLowerCase().includes(searchText.toLowerCase()) ||
        listing.csv_row['Custom label (SKU)']?.toLowerCase().includes(searchText.toLowerCase())
      );
      setFilteredListings(filtered);
    }
  }, [listings, searchText]);

  const loadListings = async () => {
    setLoading(true);
    try {
      // If currentAccount is null, get listings from all accounts
      // If currentAccount is set, get listings from specific account
      const accountId = accountState.currentAccount?.id;
      const listingsData = await listingsAPI.getListings(accountId);
      setListings(listingsData);
    } catch (error) {
      console.error('Failed to load listings:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStockStatus = (quantity: any) => {
    const qty = parseInt(quantity) || 0;
    if (qty === 0) return { label: 'Out of Stock', color: 'error' as const };
    if (qty <= 5) return { label: 'Low Stock', color: 'warning' as const };
    return { label: 'In Stock', color: 'success' as const };
  };

  const columns: GridColDef[] = [
    {
      field: 'item_id',
      headerName: 'Item Number',
      width: 120,
      renderCell: (params) => (
        <Typography variant="body2" fontWeight="bold">
          {params.value}
        </Typography>
      ),
    },
    {
      field: 'title',
      headerName: 'Title',
      width: 350,
      valueGetter: (params) => params.row.csv_row['Title'] || 'N/A',
    },
    {
      field: 'sku',
      headerName: 'SKU',
      width: 120,
      valueGetter: (params) => params.row.csv_row['Custom label (SKU)'] || 'N/A',
    },
    {
      field: 'current_price',
      headerName: 'Price',
      width: 100,
      valueGetter: (params) => {
        const price = params.row.csv_row['Current price'] || params.row.csv_row['Start price'];
        return price ? `$${price}` : 'N/A';
      },
    },
    {
      field: 'available_quantity',
      headerName: 'Available',
      width: 100,
      valueGetter: (params) => params.row.csv_row['Available quantity'] || '0',
      renderCell: (params) => {
        const quantity = params.row.csv_row['Available quantity'] || '0';
        const status = getStockStatus(quantity);
        
        return (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Typography variant="body2">
              {quantity}
            </Typography>
            <Chip
              label={status.label}
              color={status.color}
              size="small"
            />
          </Box>
        );
      },
    },
    {
      field: 'sold_quantity',
      headerName: 'Sold',
      width: 80,
      valueGetter: (params) => params.row.csv_row['Sold quantity'] || '0',
    },
    {
      field: 'watchers',
      headerName: 'Watchers',
      width: 90,
      valueGetter: (params) => params.row.csv_row['Watchers'] || '0',
    },
    {
      field: 'format',
      headerName: 'Format',
      width: 120,
      valueGetter: (params) => {
        const format = params.row.csv_row['Format'];
        if (format === 'FIXED_PRICE') return 'Buy It Now';
        return format || 'N/A';
      },
    },
    {
      field: 'end_date',
      headerName: 'End Date',
      width: 120,
      valueGetter: (params) => {
        const date = params.row.csv_row['End date'];
        return date ? new Date(date).toLocaleDateString() : 'N/A';
      },
    },
  ];

  return (
    <Box>
      <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h4" component="h1">
          Listings
        </Typography>
        
        <Box sx={{ display: 'flex', gap: 2 }}>
          <TextField
            label="Search listings"
            variant="outlined"
            size="small"
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            sx={{ minWidth: 300 }}
          />
        </Box>
      </Box>

      <Box sx={{ mb: 2 }}>
        <Typography variant="body2" color="textSecondary">
          Showing {filteredListings.length} of {listings.length} listings
        </Typography>
      </Box>

      <DataGrid
        rows={filteredListings}
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
    </Box>
  );
};

export default Listings;