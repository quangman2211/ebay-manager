import { GridColDef } from '@mui/x-data-grid';
import { Chip, Typography, Box } from '@mui/material';
import { Warning, CheckCircle, Schedule, Person, Home, LocationOn, Phone } from '@mui/icons-material';
import { tableStyles } from '../styles/config/tableStyles';
import { colors } from '../styles/common/colors';

const getStatusColor = (status?: string) => {
  switch (status) {
    case 'pending': return 'warning';
    case 'processing': return 'info';
    case 'shipped': return 'secondary';
    case 'completed': return 'success';
    default: return 'default';
  }
};

const getDaysUntilShipBy = (shipByDate: string): number => {
  if (!shipByDate) return 999;
  const shipBy = new Date(shipByDate);
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const diffTime = shipBy.getTime() - today.getTime();
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
  return diffDays;
};

const getShipByStatus = (shipByDate: string) => {
  const daysLeft = getDaysUntilShipBy(shipByDate);
  
  if (daysLeft < 0) {
    return { color: colors.error, icon: Warning, label: 'OVERDUE' };
  } else if (daysLeft <= 2) {
    return { color: colors.warning, icon: Schedule, label: 'DUE SOON' };
  }
  return { color: colors.success, icon: CheckCircle, label: null };
};

export const orderColumns: GridColDef[] = [
  {
    field: 'order_number',
    headerName: 'Order #',
    width: 110,
    valueGetter: (params) => params.row.csv_row['Order Number'] || params.row.item_id,
    renderCell: (params) => (
      <Typography variant="body2" sx={tableStyles.orderNumber}>
        {params.value}
      </Typography>
    ),
  },
  {
    field: 'item_number',
    headerName: 'Item #',
    width: 100,
    valueGetter: (params) => params.row.csv_row['Item Number'] || 'N/A',
    renderCell: (params) => (
      <Typography variant="body2" sx={tableStyles.itemNumber}>
        {params.value}
      </Typography>
    ),
  },
  {
    field: 'customer',
    headerName: 'Customer',
    width: 280,
    renderCell: (params) => {
      const row = params.row.csv_row;
      const name = row['Buyer Name'] || '';
      const username = row['Buyer Username'] || '';
      const phone = row['Ship To Phone'] || '';
      const addr1 = row['Ship To Address 1'] || '';
      const city = row['Ship To City'] || '';
      const state = row['Ship To State'] || '';
      const zip = row['Ship To Zip'] || '';
      
      return (
        <Box sx={tableStyles.customerContainer}>
          {username && (
            <Box sx={tableStyles.customerInfoRow}>
              <Person sx={tableStyles.customerIcon} />
              <Typography variant="caption" sx={tableStyles.customerText}>
                {username}
              </Typography>
            </Box>
          )}
          {name && (
            <Box sx={tableStyles.customerInfoRow}>
              <Person sx={tableStyles.customerNameIcon} />
              <Typography variant="caption" sx={tableStyles.customerNameText}>
                {name}
              </Typography>
            </Box>
          )}
          {addr1 && (
            <Box sx={tableStyles.customerInfoRow}>
              <Home sx={tableStyles.customerIcon} />
              <Typography variant="caption" sx={tableStyles.customerText}>
                {addr1}
              </Typography>
            </Box>
          )}
          {(city || state || zip) && (
            <Box sx={tableStyles.customerInfoRow}>
              <LocationOn sx={tableStyles.customerIcon} />
              <Typography variant="caption" sx={tableStyles.customerText}>
                {[city, state, zip].filter(Boolean).join(', ')}
              </Typography>
            </Box>
          )}
          {phone && (
            <Box sx={tableStyles.customerInfoRow}>
              <Phone sx={tableStyles.customerIcon} />
              <Typography variant="caption" sx={tableStyles.customerText}>
                {phone}
              </Typography>
            </Box>
          )}
        </Box>
      );
    },
  },
  {
    field: 'item_title',
    headerName: 'Item',
    width: 300,
    valueGetter: (params) => params.row.csv_row['Item Title'] || 'N/A',
    renderCell: (params) => (
      <Typography variant="body2" sx={tableStyles.itemTitle}>
        {params.value}
      </Typography>
    ),
  },
  {
    field: 'option',
    headerName: 'Opt',
    width: 80,
    valueGetter: (params) => {
      const variation = params.row.csv_row['Variation Details'] || '';
      const quantity = params.row.csv_row['Quantity'] || '1';
      
      if (quantity !== '1' && quantity !== 1) {
        return `Qty: ${quantity}`;
      }
      return variation || '-';
    },
    renderCell: (params) => (
      <Typography variant="body2" sx={tableStyles.optionText}>
        {params.value}
      </Typography>
    ),
  },
  {
    field: 'sale_date',
    headerName: 'Sale',
    width: 95,
    valueGetter: (params) => {
      const date = params.row.csv_row['Sale Date'];
      if (!date) return 'N/A';
      const d = new Date(date);
      return `${(d.getMonth() + 1).toString().padStart(2, '0')}/${d.getDate().toString().padStart(2, '0')}`;
    },
    renderCell: (params) => (
      <Typography variant="body2" sx={tableStyles.saleDateText}>
        {params.value}
      </Typography>
    ),
  },
  {
    field: 'ship_by_date',
    headerName: 'Ship By',
    width: 110,
    valueGetter: (params) => {
      const date = params.row.csv_row['Ship By Date'];
      if (!date) return 'N/A';
      const d = new Date(date);
      return `${(d.getMonth() + 1).toString().padStart(2, '0')}/${d.getDate().toString().padStart(2, '0')}`;
    },
    renderCell: (params) => {
      const dateStr = params.row.csv_row['Ship By Date'];
      if (!dateStr) return <Typography variant="body2" sx={{ fontSize: '12px' }}>N/A</Typography>;
      
      const status = getShipByStatus(dateStr);
      const IconComponent = status.icon;
      
      return (
        <Box sx={tableStyles.shipByContainer}>
          {IconComponent && <IconComponent sx={{ ...tableStyles.shipByIcon, color: status.color }} />}
          <Typography 
            variant="body2" 
            sx={{
              ...tableStyles.shipByText,
              fontWeight: status.label ? 'bold' : 'normal',
              color: status.color,
            }}
          >
            {params.value}
          </Typography>
        </Box>
      );
    },
  },
  {
    field: 'sold_for',
    headerName: 'Amount',
    width: 100,
    valueGetter: (params) => params.row.csv_row['Sold For'] || params.row.csv_row['Total Price'] || '$0',
    renderCell: (params) => (
      <Typography variant="body2" sx={tableStyles.amountText}>
        {params.value}
      </Typography>
    ),
  },
  {
    field: 'status',
    headerName: 'Status',
    width: 110,
    renderCell: (params) => {
      const status = params.row.order_status?.status || 'pending';
      return (
        <Chip
          label={status.charAt(0).toUpperCase() + status.slice(1)}
          color={getStatusColor(status) as any}
          size="medium"
          sx={tableStyles.statusChip}
        />
      );
    },
  },
];