import React, { useState, useEffect } from 'react';
import {
  DataGrid,
  GridColDef,
  GridActionsCellItem,
  GridRowSelectionModel,
} from '@mui/x-data-grid';
import {
  Box,
  Chip,
  IconButton,
  Tooltip,
  Typography,
} from '@mui/material';
import {
  Edit as EditIcon,
  Delete as DeleteIcon,
} from '@mui/icons-material';
import { Account } from '../../types';

interface AccountDataGridProps {
  accounts: Account[];
  loading: boolean;
  onEditAccount: (account: Account) => void;
  onDeleteAccount: (accountId: number) => void;
  selectedAccountIds: number[];
  onSelectionChange: (selectionModel: GridRowSelectionModel) => void;
}

/**
 * Account Data Grid Component
 * Follows Single Responsibility Principle - handles only account listing display
 */
const AccountDataGrid: React.FC<AccountDataGridProps> = ({
  accounts,
  loading,
  onEditAccount,
  onDeleteAccount,
  selectedAccountIds,
  onSelectionChange,
}) => {
  const getRelativeTime = (dateString: string | undefined): string => {
    if (!dateString) return 'Never';
    
    const date = new Date(dateString);
    const now = new Date();
    const diffInMinutes = Math.floor((now.getTime() - date.getTime()) / (1000 * 60));
    
    if (diffInMinutes < 1) return 'Just now';
    if (diffInMinutes < 60) return `${diffInMinutes}m ago`;
    
    const diffInHours = Math.floor(diffInMinutes / 60);
    if (diffInHours < 24) return `${diffInHours}h ago`;
    
    const diffInDays = Math.floor(diffInHours / 24);
    if (diffInDays < 7) return `${diffInDays}d ago`;
    
    return date.toLocaleDateString();
  };

  const columns: GridColDef[] = [
    {
      field: 'name',
      headerName: 'Account Name',
      width: 250,
      renderCell: (params) => (
        <Box>
          <Typography variant="body2" fontWeight="medium">
            {params.value}
          </Typography>
          <Typography variant="caption" color="text.secondary">
            {params.row.platform_username}
          </Typography>
        </Box>
      ),
    },
    {
      field: 'platform_username',
      headerName: 'Platform Username',
      width: 200,
    },
    {
      field: 'account_type',
      headerName: 'Type',
      width: 120,
      renderCell: (params) => (
        <Chip 
          label={params.value || 'eBay'} 
          size="small" 
          variant="outlined"
        />
      ),
    },
    {
      field: 'is_active',
      headerName: 'Status',
      width: 120,
      renderCell: (params) => (
        <Chip
          label={params.value ? 'Active' : 'Inactive'}
          size="small"
          color={params.value ? 'success' : 'error'}
        />
      ),
    },
    {
      field: 'last_sync_at',
      headerName: 'Last Update',
      width: 160,
      renderCell: (params) => (
        <Tooltip title={params.value ? `Last updated: ${new Date(params.value).toLocaleString()}` : 'No CSV imports yet'}>
          <Typography variant="body2" color="text.secondary">
            {getRelativeTime(params.value)}
          </Typography>
        </Tooltip>
      ),
    },
    {
      field: 'created_at',
      headerName: 'Created',
      width: 140,
      renderCell: (params) => (
        <Typography variant="body2" color="text.secondary">
          {new Date(params.value).toLocaleDateString()}
        </Typography>
      ),
    },
    {
      field: 'actions',
      type: 'actions',
      headerName: 'Actions',
      width: 150,
      getActions: (params) => [
        <GridActionsCellItem
          key="edit"
          icon={
            <Tooltip title="Edit Account">
              <EditIcon />
            </Tooltip>
          }
          label="Edit"
          onClick={() => onEditAccount(params.row)}
        />,
        <GridActionsCellItem
          key="delete"
          icon={
            <Tooltip title="Deactivate Account">
              <DeleteIcon />
            </Tooltip>
          }
          label="Delete"
          onClick={() => onDeleteAccount(params.row.id)}
          showInMenu
        />,
      ],
    },
  ];

  return (
    <Box sx={{ width: '100%' }}>
      <DataGrid
        rows={accounts}
        columns={columns}
        loading={loading}
        checkboxSelection
        disableRowSelectionOnClick
        rowSelectionModel={selectedAccountIds}
        onRowSelectionModelChange={onSelectionChange}
        pageSizeOptions={[25, 50, 100]}
        initialState={{
          pagination: {
            paginationModel: {
              pageSize: 25,
            },
          },
          sorting: {
            sortModel: [{ field: 'created_at', sort: 'desc' }],
          },
        }}
        sx={{
          height: 600,
          '& .MuiDataGrid-cell': {
            display: 'flex',
            alignItems: 'center',
          },
          '& .MuiDataGrid-row:hover': {
            backgroundColor: 'action.hover',
          },
        }}
        localeText={{
          noRowsLabel: 'No accounts found',
          noResultsOverlayLabel: 'No accounts match your search criteria',
        }}
      />
    </Box>
  );
};

export default AccountDataGrid;