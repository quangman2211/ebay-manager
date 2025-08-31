import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  Chip,
  IconButton,
  Tooltip,
} from '@mui/material';
import { DataGrid, GridColDef, GridActionsCellItem } from '@mui/x-data-grid';
import { Edit as EditIcon, Analytics as MetricsIcon } from '@mui/icons-material';
import { accountsAPI, listingsAPI } from '../services/api';
import type { Account, Listing } from '../types';
import ListingEditModal from '../components/listings/ListingEditModal';
import InlineEditableField from '../components/listings/InlineEditableField';
import ListingStatusToggle from '../components/listings/ListingStatusToggle';
import ListingPerformanceIndicator from '../components/listings/ListingPerformanceIndicator';

const Listings: React.FC = () => {
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [selectedAccount, setSelectedAccount] = useState<number | ''>('');
  const [searchText, setSearchText] = useState('');
  const [listings, setListings] = useState<Listing[]>([]);
  const [filteredListings, setFilteredListings] = useState<Listing[]>([]);
  const [loading, setLoading] = useState(false);
  
  // Modal states
  const [editModalOpen, setEditModalOpen] = useState(false);
  const [selectedListing, setSelectedListing] = useState<Listing | null>(null);

  useEffect(() => {
    loadAccounts();
  }, []);

  useEffect(() => {
    if (selectedAccount) {
      loadListings();
    }
  }, [selectedAccount]);

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

  const loadListings = async () => {
    if (!selectedAccount) return;
    
    setLoading(true);
    try {
      const listingsData = await listingsAPI.getListings(selectedAccount as number);
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

  const handleEditListing = (listing: Listing) => {
    setSelectedListing(listing);
    setEditModalOpen(true);
  };

  const handleCloseEditModal = () => {
    setEditModalOpen(false);
    setSelectedListing(null);
  };

  const handleListingUpdated = () => {
    loadListings(); // Reload listings after update
  };

  const handleInlineFieldUpdate = async (listingId: number, field: string, value: string) => {
    try {
      await listingsAPI.updateListingField(listingId, field, value);
      // Update local state to reflect changes immediately
      setListings(prevListings => 
        prevListings.map(listing => {
          if (listing.id === listingId) {
            const updatedCsvRow = { ...listing.csv_row };
            if (field === 'price') {
              updatedCsvRow['Current price'] = value.replace('$', '');
              updatedCsvRow['Start price'] = value.replace('$', '');
            } else if (field === 'quantity') {
              updatedCsvRow['Available quantity'] = value;
            } else if (field === 'status') {
              updatedCsvRow['Status'] = value;
            }
            return { ...listing, csv_row: updatedCsvRow };
          }
          return listing;
        })
      );
    } catch (error) {
      console.error('Failed to update field:', error);
      throw error;
    }
  };

  const validatePrice = (value: string): string | null => {
    const price = parseFloat(value.replace('$', '').replace(',', ''));
    if (isNaN(price) || price <= 0) {
      return 'Price must be a valid positive number';
    }
    return null;
  };

  const validateQuantity = (value: string): string | null => {
    const qty = parseInt(value);
    if (isNaN(qty) || qty < 0) {
      return 'Quantity must be a valid non-negative number';
    }
    return null;
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
      width: 150,
      renderCell: (params) => {
        const price = params.row.csv_row['Current price'] || params.row.csv_row['Start price'];
        if (!price) return 'N/A';
        
        return (
          <InlineEditableField
            value={price}
            type="price"
            onSave={(value) => handleInlineFieldUpdate(params.row.id, 'price', value)}
            validation={validatePrice}
            placeholder="Enter price"
          />
        );
      },
    },
    {
      field: 'available_quantity',
      headerName: 'Available',
      width: 180,
      renderCell: (params) => {
        const quantity = params.row.csv_row['Available quantity'] || '0';
        const status = getStockStatus(quantity);
        
        return (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, width: '100%' }}>
            <InlineEditableField
              value={quantity}
              type="number"
              onSave={(value) => handleInlineFieldUpdate(params.row.id, 'quantity', value)}
              validation={validateQuantity}
              placeholder="0"
            />
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
      field: 'performance',
      headerName: 'Performance',
      width: 150,
      renderCell: (params) => (
        <ListingPerformanceIndicator listing={params.row} compact={true} />
      ),
      sortable: false,
      filterable: false,
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
      field: 'status',
      headerName: 'Status',
      width: 120,
      renderCell: (params) => {
        const currentStatus = params.row.csv_row['Status'] || 'active';
        
        return (
          <ListingStatusToggle
            currentStatus={currentStatus}
            onStatusChange={(newStatus) => handleInlineFieldUpdate(params.row.id, 'status', newStatus)}
          />
        );
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
    {
      field: 'actions',
      headerName: 'Actions',
      width: 120,
      type: 'actions',
      getActions: (params) => [
        <GridActionsCellItem
          icon={
            <Tooltip title="Edit Listing">
              <EditIcon />
            </Tooltip>
          }
          label="Edit"
          onClick={() => handleEditListing(params.row)}
          color="inherit"
        />,
        <GridActionsCellItem
          icon={
            <Tooltip title="View Metrics">
              <MetricsIcon />
            </Tooltip>
          }
          label="Metrics"
          onClick={() => handleEditListing(params.row)} // For now, same as edit
          color="inherit"
        />,
      ],
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

      {/* Edit Modal */}
      <ListingEditModal
        open={editModalOpen}
        onClose={handleCloseEditModal}
        listing={selectedListing}
        onSave={handleListingUpdated}
      />
    </Box>
  );
};

export default Listings;