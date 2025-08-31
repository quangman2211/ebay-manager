import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Grid,
  Typography,
  Box,
  Alert,
  Divider,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  InputAdornment,
} from '@mui/material';
import { listingsAPI } from '../../services/api';
import type { Listing } from '../../types';

interface ListingEditModalProps {
  open: boolean;
  onClose: () => void;
  listing: Listing | null;
  onSave: () => void;
}

interface ListingFormData {
  title: string;
  price: string;
  quantity: string;
  status: string;
  description: string;
}

interface ListingMetrics {
  sell_through_rate: number;
  watchers_count: number;
  stock_status: string;
  days_listed: number;
  price_competitiveness: string;
}

const ListingEditModal: React.FC<ListingEditModalProps> = ({
  open,
  onClose,
  listing,
  onSave,
}) => {
  const [formData, setFormData] = useState<ListingFormData>({
    title: '',
    price: '',
    quantity: '',
    status: '',
    description: '',
  });

  const [metrics, setMetrics] = useState<ListingMetrics | null>(null);
  const [loading, setLoading] = useState(false);
  const [metricsLoading, setMetricsLoading] = useState(false);
  const [error, setError] = useState<string>('');
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    if (listing) {
      setFormData({
        title: listing.csv_row['Title'] || '',
        price: listing.csv_row['Current price'] || listing.csv_row['Start price'] || '',
        quantity: listing.csv_row['Available quantity'] || '',
        status: listing.csv_row['Status'] || 'active',
        description: listing.csv_row['Description'] || '',
      });

      // Load performance metrics
      loadMetrics();
    }
  }, [listing]);

  const loadMetrics = async () => {
    if (!listing) return;

    setMetricsLoading(true);
    try {
      const metricsData = await listingsAPI.getListingMetrics(listing.id);
      setMetrics(metricsData);
    } catch (error) {
      console.error('Failed to load metrics:', error);
    } finally {
      setMetricsLoading(false);
    }
  };

  const validateForm = (): boolean => {
    const errors: Record<string, string> = {};

    if (!formData.title.trim()) {
      errors.title = 'Title is required';
    } else if (formData.title.length > 255) {
      errors.title = 'Title must be less than 255 characters';
    }

    if (!formData.price.trim()) {
      errors.price = 'Price is required';
    } else {
      const price = parseFloat(formData.price.replace('$', '').replace(',', ''));
      if (isNaN(price) || price <= 0) {
        errors.price = 'Price must be a valid positive number';
      }
    }

    if (!formData.quantity.trim()) {
      errors.quantity = 'Quantity is required';
    } else {
      const qty = parseInt(formData.quantity);
      if (isNaN(qty) || qty < 0) {
        errors.quantity = 'Quantity must be a valid non-negative number';
      }
    }

    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSave = async () => {
    if (!listing || !validateForm()) return;

    setLoading(true);
    setError('');

    try {
      // Prepare updates (only include changed fields)
      const updates: Partial<ListingFormData> = {};
      
      if (formData.title !== (listing.csv_row['Title'] || '')) {
        updates.title = formData.title;
      }
      if (formData.price !== (listing.csv_row['Current price'] || listing.csv_row['Start price'] || '')) {
        updates.price = formData.price;
      }
      if (formData.quantity !== (listing.csv_row['Available quantity'] || '')) {
        updates.quantity = formData.quantity;
      }
      if (formData.status !== (listing.csv_row['Status'] || 'active')) {
        updates.status = formData.status;
      }
      if (formData.description !== (listing.csv_row['Description'] || '')) {
        updates.description = formData.description;
      }

      if (Object.keys(updates).length === 0) {
        onClose();
        return;
      }

      await listingsAPI.updateListing(listing.id, updates);
      onSave();
      onClose();
    } catch (error: any) {
      setError(error.response?.data?.detail || 'Failed to update listing');
    } finally {
      setLoading(false);
    }
  };

  const handleFieldChange = (field: keyof ListingFormData, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    // Clear validation error for this field
    if (validationErrors[field]) {
      setValidationErrors(prev => ({ ...prev, [field]: '' }));
    }
  };

  const getStockStatusColor = (status: string): 'success' | 'warning' | 'error' => {
    switch (status) {
      case 'in_stock': return 'success';
      case 'low_stock': return 'warning';
      case 'out_of_stock': return 'error';
      default: return 'warning';
    }
  };

  const getPriceCompetitivenessColor = (competitiveness: string): 'success' | 'warning' | 'error' | 'info' => {
    switch (competitiveness) {
      case 'competitive': return 'success';
      case 'attractive': return 'info';
      case 'moderate': return 'warning';
      case 'needs_review': return 'error';
      default: return 'warning';
    }
  };

  if (!listing) return null;

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="md"
      fullWidth
      PaperProps={{
        sx: { minHeight: '600px' }
      }}
    >
      <DialogTitle>
        <Typography variant="h6">
          Edit Listing - {listing.item_id}
        </Typography>
      </DialogTitle>

      <DialogContent>
        <Box sx={{ mt: 2 }}>
          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}

          {/* Performance Metrics Card */}
          <Card sx={{ mb: 3, bgcolor: 'background.default' }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Performance Metrics
              </Typography>
              {metricsLoading ? (
                <Box sx={{ display: 'flex', justifyContent: 'center', p: 2 }}>
                  <CircularProgress size={24} />
                </Box>
              ) : metrics ? (
                <Grid container spacing={2}>
                  <Grid item xs={12} sm={6} md={3}>
                    <Box sx={{ textAlign: 'center' }}>
                      <Typography variant="h4" color="primary">
                        {metrics.sell_through_rate}%
                      </Typography>
                      <Typography variant="body2" color="textSecondary">
                        Sell Through Rate
                      </Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={12} sm={6} md={3}>
                    <Box sx={{ textAlign: 'center' }}>
                      <Typography variant="h4" color="primary">
                        {metrics.watchers_count}
                      </Typography>
                      <Typography variant="body2" color="textSecondary">
                        Watchers
                      </Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={12} sm={6} md={3}>
                    <Box sx={{ textAlign: 'center' }}>
                      <Chip
                        label={metrics.stock_status.replace('_', ' ').toUpperCase()}
                        color={getStockStatusColor(metrics.stock_status)}
                        size="small"
                      />
                      <Typography variant="body2" color="textSecondary" sx={{ mt: 1 }}>
                        Stock Status
                      </Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={12} sm={6} md={3}>
                    <Box sx={{ textAlign: 'center' }}>
                      <Chip
                        label={metrics.price_competitiveness.replace('_', ' ').toUpperCase()}
                        color={getPriceCompetitivenessColor(metrics.price_competitiveness)}
                        size="small"
                      />
                      <Typography variant="body2" color="textSecondary" sx={{ mt: 1 }}>
                        Price Rating
                      </Typography>
                    </Box>
                  </Grid>
                </Grid>
              ) : (
                <Alert severity="info">Unable to load performance metrics</Alert>
              )}
            </CardContent>
          </Card>

          <Divider sx={{ mb: 3 }} />

          {/* Form Fields */}
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Title"
                value={formData.title}
                onChange={(e) => handleFieldChange('title', e.target.value)}
                error={!!validationErrors.title}
                helperText={validationErrors.title}
                multiline
                rows={2}
              />
            </Grid>

            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Price"
                value={formData.price}
                onChange={(e) => handleFieldChange('price', e.target.value)}
                error={!!validationErrors.price}
                helperText={validationErrors.price}
                InputProps={{
                  startAdornment: <InputAdornment position="start">$</InputAdornment>,
                }}
              />
            </Grid>

            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Quantity"
                type="number"
                value={formData.quantity}
                onChange={(e) => handleFieldChange('quantity', e.target.value)}
                error={!!validationErrors.quantity}
                helperText={validationErrors.quantity}
                inputProps={{ min: 0 }}
              />
            </Grid>

            <Grid item xs={12} sm={6}>
              <FormControl fullWidth>
                <InputLabel>Status</InputLabel>
                <Select
                  value={formData.status}
                  label="Status"
                  onChange={(e) => handleFieldChange('status', e.target.value)}
                >
                  <MenuItem value="active">Active</MenuItem>
                  <MenuItem value="inactive">Inactive</MenuItem>
                  <MenuItem value="ended">Ended</MenuItem>
                  <MenuItem value="sold">Sold</MenuItem>
                </Select>
              </FormControl>
            </Grid>

            <Grid item xs={12} sm={6}>
              <Box sx={{ pt: 2 }}>
                <Typography variant="body2" color="textSecondary">
                  Days Listed: {metrics?.days_listed || 0} days
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  Item ID: {listing.item_id}
                </Typography>
              </Box>
            </Grid>

            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Description"
                value={formData.description}
                onChange={(e) => handleFieldChange('description', e.target.value)}
                multiline
                rows={4}
              />
            </Grid>
          </Grid>
        </Box>
      </DialogContent>

      <DialogActions>
        <Button onClick={onClose} disabled={loading}>
          Cancel
        </Button>
        <Button 
          onClick={handleSave} 
          variant="contained" 
          disabled={loading}
          startIcon={loading && <CircularProgress size={16} />}
        >
          {loading ? 'Saving...' : 'Save Changes'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default ListingEditModal;