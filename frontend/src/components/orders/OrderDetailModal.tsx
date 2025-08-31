import React from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  Box,
  Grid,
  Divider,
  Chip,
} from '@mui/material';
import {
  Person,
  Home,
  Phone,
  Email,
  LocalShipping,
  Payment,
  Info,
} from '@mui/icons-material';
import { colors } from '../../styles/common/colors';
import { spacing } from '../../styles/common/spacing';
import OrderNotesManager from './OrderNotesManager';
import OrderHistoryTimeline from './OrderHistoryTimeline';
import type { Order, OrderNote } from '../../types';

interface OrderDetailModalProps {
  order: Order | null;
  open: boolean;
  onClose: () => void;
  onNotesUpdate?: (orderId: number, notes: OrderNote[]) => void;
}

interface IOrderDetailView {
  order: Order;
}

const OrderDetailView: React.FC<IOrderDetailView> = ({ order }) => {
  const csvData = order.csv_row;
  const status = order.order_status?.status || 'pending';

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending': return colors.warning;
      case 'processing': return colors.info;
      case 'shipped': return colors.secondary;
      case 'completed': return colors.success;
      default: return colors.text.secondary;
    }
  };

  const InfoSection: React.FC<{ title: string; icon: React.ElementType; children: React.ReactNode }> = 
    ({ title, icon: Icon, children }) => (
      <Box sx={{ marginBottom: spacing.medium }}>
        <Box sx={{ display: 'flex', alignItems: 'center', marginBottom: spacing.small }}>
          <Icon sx={{ marginRight: spacing.small, color: colors.primary }} />
          <Typography variant="h6" sx={{ fontWeight: 600 }}>
            {title}
          </Typography>
        </Box>
        {children}
      </Box>
    );

  const InfoRow: React.FC<{ label: string; value: string | undefined }> = ({ label, value }) => (
    <Grid container sx={{ marginBottom: spacing.xsmall }}>
      <Grid item xs={4}>
        <Typography variant="body2" sx={{ fontWeight: 500, color: colors.text.secondary }}>
          {label}:
        </Typography>
      </Grid>
      <Grid item xs={8}>
        <Typography variant="body2">
          {value || 'N/A'}
        </Typography>
      </Grid>
    </Grid>
  );

  return (
    <Box>
      <InfoSection title="Order Information" icon={Info}>
        <InfoRow label="Order Number" value={csvData['Order Number']} />
        <InfoRow label="Item Number" value={csvData['Item Number']} />
        <InfoRow label="Item Title" value={csvData['Item Title']} />
        <InfoRow label="Variation" value={csvData['Variation Details']} />
        <InfoRow label="Quantity" value={csvData['Quantity']} />
        <InfoRow label="Sale Date" value={csvData['Sale Date']} />
        <InfoRow label="Ship By Date" value={csvData['Ship By Date']} />
        <Box sx={{ marginTop: spacing.small }}>
          <Typography variant="body2" sx={{ fontWeight: 500, marginBottom: spacing.xsmall }}>
            Status:
          </Typography>
          <Chip
            label={status.charAt(0).toUpperCase() + status.slice(1)}
            sx={{
              backgroundColor: getStatusColor(status),
              color: colors.background.paper,
              fontWeight: 600,
            }}
          />
        </Box>
      </InfoSection>

      <Divider sx={{ marginY: spacing.medium }} />

      <InfoSection title="Customer Information" icon={Person}>
        <InfoRow label="Name" value={csvData['Buyer Name']} />
        <InfoRow label="Username" value={csvData['Buyer Username']} />
        <InfoRow label="Email" value={csvData['Buyer Email']} />
      </InfoSection>

      <Divider sx={{ marginY: spacing.medium }} />

      <InfoSection title="Shipping Address" icon={Home}>
        <InfoRow label="Address 1" value={csvData['Ship To Address 1']} />
        <InfoRow label="Address 2" value={csvData['Ship To Address 2']} />
        <InfoRow label="City" value={csvData['Ship To City']} />
        <InfoRow label="State" value={csvData['Ship To State']} />
        <InfoRow label="ZIP Code" value={csvData['Ship To Zip']} />
        <InfoRow label="Country" value={csvData['Ship To Country']} />
        <InfoRow label="Phone" value={csvData['Ship To Phone']} />
      </InfoSection>

      <Divider sx={{ marginY: spacing.medium }} />

      <InfoSection title="Payment Information" icon={Payment}>
        <InfoRow label="Sold For" value={csvData['Sold For']} />
        <InfoRow label="Total Price" value={csvData['Total Price']} />
        <InfoRow label="Shipping Cost" value={csvData['Shipping Cost']} />
        <InfoRow label="Payment Method" value={csvData['Payment Method']} />
        <InfoRow label="Checkout Date" value={csvData['Checkout Date']} />
      </InfoSection>

      <Divider sx={{ marginY: spacing.medium }} />

      <InfoSection title="Shipping Information" icon={LocalShipping}>
        <InfoRow label="Shipping Service" value={csvData['Shipping Service']} />
        <InfoRow label="Tracking Number" value={csvData['Tracking Number']} />
        <InfoRow label="Feedback Left" value={csvData['Feedback Left']} />
        <InfoRow label="Feedback Received" value={csvData['Feedback Received']} />
      </InfoSection>
    </Box>
  );
};

interface IOrderDetailViewWithNotes extends IOrderDetailView {
  onNotesUpdate?: (orderId: number, notes: OrderNote[]) => void;
}

const OrderDetailViewWithNotes: React.FC<IOrderDetailViewWithNotes> = ({ order, onNotesUpdate }) => (
  <Box>
    <OrderDetailView order={order} />
    
    <Divider sx={{ marginY: spacing.large }} />
    <OrderHistoryTimeline order={order} />
    
    <Divider sx={{ marginY: spacing.large }} />
    {onNotesUpdate && (
      <OrderNotesManager
        order={order}
        onNotesUpdate={onNotesUpdate}
      />
    )}
  </Box>
);

const OrderDetailModal: React.FC<OrderDetailModalProps> = ({ order, open, onClose, onNotesUpdate }) => {
  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="md"
      fullWidth
      sx={{
        '& .MuiDialog-paper': {
          maxHeight: '80vh',
          overflow: 'hidden',
        },
      }}
    >
      <DialogTitle sx={{ 
        backgroundColor: colors.background.default,
        borderBottom: `1px solid ${colors.divider}`,
        paddingY: spacing.medium,
      }}>
        <Typography variant="h5" sx={{ fontWeight: 600 }}>
          Order Details
        </Typography>
        {order && (
          <Typography variant="body2" sx={{ color: colors.text.secondary, marginTop: spacing.xsmall }}>
            {order.csv_row['Order Number'] || order.item_id}
          </Typography>
        )}
      </DialogTitle>

      <DialogContent sx={{ 
        padding: spacing.large,
        overflow: 'auto',
      }}>
        {order && <OrderDetailViewWithNotes order={order} onNotesUpdate={onNotesUpdate} />}
      </DialogContent>

      <DialogActions sx={{ 
        padding: spacing.medium,
        borderTop: `1px solid ${colors.divider}`,
        backgroundColor: colors.background.default,
      }}>
        <Button onClick={onClose} variant="contained" color="primary">
          Close
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default OrderDetailModal;