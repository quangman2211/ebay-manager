# Frontend Phase 5: Product & Supplier Hub Implementation

## Overview
Implement comprehensive Product & Supplier management interface with inventory tracking, supplier relationship management, product-listing synchronization, and intelligent reorder recommendations. Includes supplier performance analytics and streamlined product sourcing workflow.

## SOLID/YAGNI Compliance Strategy

### Single Responsibility Principle (SRP)
- **ProductHub**: Only handle product catalog display and management
- **SupplierDirectory**: Only manage supplier information and relationships  
- **InventoryTracker**: Only track stock levels and movement
- **ProductEditor**: Only edit individual product information
- **SupplierPerformance**: Only calculate and display supplier metrics
- **ReorderManager**: Only handle reorder point calculations and recommendations

### Open/Closed Principle (OCP)
- **Product Import Sources**: Extensible to support multiple CSV formats
- **Supplier Metrics**: Add new performance indicators without core changes
- **Inventory Alerts**: Configurable alert rules through strategy pattern
- **Product Matching**: Multiple product identification algorithms

### Liskov Substitution Principle (LSP)
- **Product Providers**: CSV and manual product sources interchangeable
- **Supplier Data Sources**: Different supplier information providers substitutable
- **Inventory Calculators**: All stock calculation methods follow same interface

### Interface Segregation Principle (ISP)
- **Product Interfaces**: Separate read-only vs editable product operations
- **Supplier Interfaces**: Different interfaces for basic info vs performance analytics
- **Inventory Interfaces**: Segregate tracking vs management operations

### Dependency Inversion Principle (DIP)
- **Product Services**: Components depend on abstract product interfaces
- **Supplier Services**: Configurable supplier data providers
- **Inventory Services**: Pluggable stock calculation engines

## Product & Supplier Architecture

### Main Product Hub Layout
```typescript
// src/components/products/ProductHub.tsx - Single Responsibility: Product interface composition
import React, { useState, useMemo } from 'react';
import { 
  Box, 
  Container, 
  Paper, 
  Tabs, 
  Tab, 
  Grid,
  Typography,
  Button,
  Card,
  CardContent
} from '@mui/material';
import {
  Inventory,
  People,
  TrendingUp,
  Warning,
  AddCircle
} from '@mui/icons-material';
import { ProductCatalog } from './ProductCatalog';
import { SupplierDirectory } from './SupplierDirectory';
import { InventoryDashboard } from './InventoryDashboard';
import { ReorderRecommendations } from './ReorderRecommendations';
import { ProductSupplierAnalytics } from './ProductSupplierAnalytics';
import { useProductData } from '../../hooks/useProductData';
import { useSupplierData } from '../../hooks/useSupplierData';
import { useInventoryData } from '../../hooks/useInventoryData';

type ProductTab = 'catalog' | 'suppliers' | 'inventory' | 'reorders' | 'analytics';

interface QuickStatsProps {
  totalProducts: number;
  activeSuppliers: number;
  lowStockItems: number;
  reorderAlerts: number;
}

const QuickStats: React.FC<QuickStatsProps> = ({
  totalProducts,
  activeSuppliers,
  lowStockItems,
  reorderAlerts
}) => {
  const stats = [
    {
      label: 'Total Products',
      value: totalProducts,
      icon: <Inventory />,
      color: 'primary' as const
    },
    {
      label: 'Active Suppliers',
      value: activeSuppliers,
      icon: <People />,
      color: 'success' as const
    },
    {
      label: 'Low Stock Items',
      value: lowStockItems,
      icon: <Warning />,
      color: 'warning' as const
    },
    {
      label: 'Reorder Alerts',
      value: reorderAlerts,
      icon: <TrendingUp />,
      color: 'error' as const
    }
  ];

  return (
    <Grid container spacing={2} sx={{ mb: 3 }}>
      {stats.map((stat, index) => (
        <Grid item xs={12} sm={6} md={3} key={index}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    {stat.label}
                  </Typography>
                  <Typography variant="h4" component="div">
                    {stat.value}
                  </Typography>
                </Box>
                <Box sx={{ 
                  p: 1, 
                  borderRadius: 1, 
                  bgcolor: `${stat.color}.light`,
                  color: `${stat.color}.main`
                }}>
                  {stat.icon}
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      ))}
    </Grid>
  );
};

export const ProductHub: React.FC = () => {
  const [activeTab, setActiveTab] = useState<ProductTab>('catalog');
  const [selectedProducts, setSelectedProducts] = useState<string[]>([]);

  const { 
    products, 
    productStats, 
    loading: productsLoading, 
    refresh: refreshProducts 
  } = useProductData();

  const { 
    suppliers, 
    supplierStats, 
    loading: suppliersLoading, 
    refresh: refreshSuppliers 
  } = useSupplierData();

  const { 
    inventory, 
    inventoryStats, 
    lowStockAlerts,
    reorderRecommendations,
    loading: inventoryLoading, 
    refresh: refreshInventory 
  } = useInventoryData();

  const handleTabChange = (_: React.SyntheticEvent, newValue: ProductTab) => {
    setActiveTab(newValue);
    setSelectedProducts([]);
  };

  const handleRefreshAll = async () => {
    await Promise.all([
      refreshProducts(),
      refreshSuppliers(),
      refreshInventory()
    ]);
  };

  const isLoading = productsLoading || suppliersLoading || inventoryLoading;

  return (
    <Container maxWidth="xl" sx={{ py: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h4" component="h1" gutterBottom>
            Product & Supplier Hub
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Manage your product catalog, supplier relationships, and inventory levels
          </Typography>
        </Box>
        
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            variant="outlined"
            onClick={handleRefreshAll}
            disabled={isLoading}
          >
            Refresh Data
          </Button>
          <Button
            variant="contained"
            startIcon={<AddCircle />}
            onClick={() => {
              // Open product creation dialog
            }}
          >
            Add Product
          </Button>
        </Box>
      </Box>

      {/* Quick Stats */}
      <QuickStats
        totalProducts={productStats.total}
        activeSuppliers={supplierStats.active}
        lowStockItems={inventoryStats.lowStock}
        reorderAlerts={reorderRecommendations.length}
      />

      {/* Tab Navigation */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={activeTab} onChange={handleTabChange}>
          <Tab 
            label={`Product Catalog (${productStats.total})`} 
            value="catalog"
            icon={<Inventory />}
            iconPosition="start"
          />
          <Tab 
            label={`Suppliers (${supplierStats.active})`} 
            value="suppliers"
            icon={<People />}
            iconPosition="start"
          />
          <Tab 
            label={`Inventory (${inventoryStats.lowStock} alerts)`} 
            value="inventory"
            icon={<Warning />}
            iconPosition="start"
          />
          <Tab 
            label={`Reorders (${reorderRecommendations.length})`} 
            value="reorders"
            icon={<TrendingUp />}
            iconPosition="start"
          />
          <Tab 
            label="Analytics" 
            value="analytics"
            icon={<TrendingUp />}
            iconPosition="start"
          />
        </Tabs>
      </Box>

      {/* Tab Content */}
      <Box>
        {activeTab === 'catalog' && (
          <ProductCatalog
            products={products}
            loading={productsLoading}
            selectedProducts={selectedProducts}
            onSelectionChange={setSelectedProducts}
            onRefresh={refreshProducts}
          />
        )}
        
        {activeTab === 'suppliers' && (
          <SupplierDirectory
            suppliers={suppliers}
            loading={suppliersLoading}
            onRefresh={refreshSuppliers}
          />
        )}
        
        {activeTab === 'inventory' && (
          <InventoryDashboard
            inventory={inventory}
            lowStockAlerts={lowStockAlerts}
            loading={inventoryLoading}
            onRefresh={refreshInventory}
          />
        )}
        
        {activeTab === 'reorders' && (
          <ReorderRecommendations
            recommendations={reorderRecommendations}
            loading={inventoryLoading}
            onRefresh={refreshInventory}
          />
        )}
        
        {activeTab === 'analytics' && (
          <ProductSupplierAnalytics
            productStats={productStats}
            supplierStats={supplierStats}
            inventoryStats={inventoryStats}
            loading={isLoading}
          />
        )}
      </Box>
    </Container>
  );
};
```

### Product Catalog Component
```typescript
// src/components/products/ProductCatalog.tsx - Single Responsibility: Product catalog display
import React, { useState } from 'react';
import {
  Card,
  CardHeader,
  CardContent,
  Typography,
  Box,
  Chip,
  IconButton,
  Avatar,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  Grid
} from '@mui/material';
import {
  Edit,
  Visibility,
  Link as LinkIcon,
  Inventory2,
  AttachMoney,
  Category,
  FilterList,
  Search
} from '@mui/icons-material';
import { DataTable, TableColumn } from '../common/DataTable';
import { StatusBadge } from '../common/StatusBadge';
import { Product, Supplier } from '../../types';
import { formatCurrency, formatDate } from '../../utils/formatters';

interface ProductFilters {
  search: string;
  category: string;
  supplier: string;
  status: string;
  stockLevel: 'all' | 'low' | 'out' | 'adequate';
}

interface ProductCatalogProps {
  products: Product[];
  loading: boolean;
  selectedProducts: string[];
  onSelectionChange: (productIds: string[]) => void;
  onRefresh: () => void;
}

export const ProductCatalog: React.FC<ProductCatalogProps> = ({
  products,
  loading,
  selectedProducts,
  onSelectionChange,
  onRefresh
}) => {
  const [filters, setFilters] = useState<ProductFilters>({
    search: '',
    category: '',
    supplier: '',
    status: '',
    stockLevel: 'all'
  });
  
  const [showFilters, setShowFilters] = useState(false);

  const getStockStatusColor = (level: number, reorderPoint: number) => {
    if (level === 0) return 'error';
    if (level <= reorderPoint) return 'warning';
    return 'success';
  };

  const getStockStatusText = (level: number, reorderPoint: number) => {
    if (level === 0) return 'Out of Stock';
    if (level <= reorderPoint) return 'Low Stock';
    return 'In Stock';
  };

  const filteredProducts = products.filter(product => {
    if (filters.search && !product.name.toLowerCase().includes(filters.search.toLowerCase()) 
        && !product.sku.toLowerCase().includes(filters.search.toLowerCase())) return false;
    if (filters.category && product.category !== filters.category) return false;
    if (filters.supplier && product.supplierId !== filters.supplier) return false;
    if (filters.status && product.status !== filters.status) return false;
    if (filters.stockLevel !== 'all') {
      const stockLevel = product.inventory?.currentStock || 0;
      const reorderPoint = product.inventory?.reorderPoint || 0;
      switch (filters.stockLevel) {
        case 'out': if (stockLevel > 0) return false; break;
        case 'low': if (stockLevel === 0 || stockLevel > reorderPoint) return false; break;
        case 'adequate': if (stockLevel <= reorderPoint) return false; break;
      }
    }
    return true;
  });

  const columns: TableColumn<Product>[] = [
    {
      id: 'image',
      label: '',
      accessor: (product) => (
        <Avatar
          src={product.primaryImageUrl}
          variant="rounded"
          sx={{ width: 48, height: 48 }}
        />
      ),
      width: 60
    },
    {
      id: 'product',
      label: 'Product',
      accessor: (product) => (
        <Box>
          <Typography variant="body2" fontWeight="medium" noWrap>
            {product.name}
          </Typography>
          <Typography variant="caption" color="text.secondary">
            SKU: {product.sku}
          </Typography>
          <Box sx={{ display: 'flex', gap: 0.5, mt: 0.5 }}>
            <Chip
              label={product.category}
              size="small"
              variant="outlined"
              color="primary"
            />
            {product.linkedListings.length > 0 && (
              <Chip
                icon={<LinkIcon />}
                label={`${product.linkedListings.length} listings`}
                size="small"
                variant="outlined"
                color="info"
              />
            )}
          </Box>
        </Box>
      ),
      width: 280
    },
    {
      id: 'supplier',
      label: 'Supplier',
      accessor: (product) => (
        <Box>
          <Typography variant="body2">
            {product.supplier.name}
          </Typography>
          <Typography variant="caption" color="text.secondary">
            {product.supplier.country}
          </Typography>
        </Box>
      ),
      width: 140
    },
    {
      id: 'pricing',
      label: 'Pricing',
      accessor: (product) => (
        <Box>
          <Typography variant="body2" fontWeight="medium">
            Cost: {formatCurrency(product.costPrice)}
          </Typography>
          <Typography variant="body2" color="success.main">
            Sell: {formatCurrency(product.sellingPrice)}
          </Typography>
          <Typography variant="caption" color="text.secondary">
            Margin: {(((product.sellingPrice - product.costPrice) / product.sellingPrice) * 100).toFixed(1)}%
          </Typography>
        </Box>
      ),
      width: 120,
      align: 'right'
    },
    {
      id: 'inventory',
      label: 'Inventory',
      accessor: (product) => {
        const stock = product.inventory?.currentStock || 0;
        const reorderPoint = product.inventory?.reorderPoint || 0;
        const statusColor = getStockStatusColor(stock, reorderPoint);
        const statusText = getStockStatusText(stock, reorderPoint);
        
        return (
          <Box>
            <Typography variant="body2" fontWeight="medium">
              {stock} units
            </Typography>
            <Chip
              label={statusText}
              size="small"
              color={statusColor}
              variant={stock === 0 ? 'filled' : 'outlined'}
            />
            <Typography variant="caption" color="text.secondary" display="block">
              Reorder at: {reorderPoint}
            </Typography>
          </Box>
        );
      },
      width: 120
    },
    {
      id: 'performance',
      label: 'Performance',
      accessor: (product) => (
        <Box>
          <Typography variant="body2">
            {product.performance.totalSold} sold
          </Typography>
          <Typography variant="caption" color="text.secondary">
            Revenue: {formatCurrency(product.performance.totalRevenue)}
          </Typography>
          <Typography variant="caption" color="text.secondary" display="block">
            Last sold: {product.performance.lastSoldDate ? formatDate(product.performance.lastSoldDate) : 'Never'}
          </Typography>
        </Box>
      ),
      width: 140
    },
    {
      id: 'status',
      label: 'Status',
      accessor: (product) => (
        <StatusBadge status={product.status} />
      ),
      width: 100
    },
    {
      id: 'actions',
      label: 'Actions',
      accessor: (product) => (
        <Box sx={{ display: 'flex', gap: 0.5 }}>
          <IconButton
            size="small"
            onClick={(e) => {
              e.stopPropagation();
              // View product details
            }}
            title="View Details"
          >
            <Visibility fontSize="small" />
          </IconButton>
          
          <IconButton
            size="small"
            onClick={(e) => {
              e.stopPropagation();
              // Edit product
            }}
            title="Edit Product"
            color="primary"
          >
            <Edit fontSize="small" />
          </IconButton>
          
          <IconButton
            size="small"
            onClick={(e) => {
              e.stopPropagation();
              // View linked listings
            }}
            title="View Listings"
            color="info"
          >
            <LinkIcon fontSize="small" />
          </IconButton>
        </Box>
      ),
      width: 120
    }
  ];

  return (
    <Card>
      <CardHeader
        title="Product Catalog"
        subheader={`${filteredProducts.length} products (${products.length} total)`}
        action={
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Button
              variant="outlined"
              startIcon={<FilterList />}
              onClick={() => setShowFilters(!showFilters)}
            >
              Filters
            </Button>
            <Button
              variant="contained"
              onClick={() => {
                // Open product creation dialog
              }}
            >
              Add Product
            </Button>
          </Box>
        }
      />
      
      {/* Filters */}
      {showFilters && (
        <CardContent sx={{ pt: 0, pb: 1 }}>
          <Grid container spacing={2}>
            <Grid item xs={12} md={3}>
              <TextField
                fullWidth
                label="Search"
                placeholder="Product name or SKU"
                value={filters.search}
                onChange={(e) => setFilters({ ...filters, search: e.target.value })}
                InputProps={{
                  startAdornment: <Search sx={{ mr: 1, color: 'text.secondary' }} />
                }}
                size="small"
              />
            </Grid>
            
            <Grid item xs={12} md={2}>
              <FormControl fullWidth size="small">
                <InputLabel>Category</InputLabel>
                <Select
                  value={filters.category}
                  label="Category"
                  onChange={(e) => setFilters({ ...filters, category: e.target.value })}
                >
                  <MenuItem value="">All Categories</MenuItem>
                  <MenuItem value="electronics">Electronics</MenuItem>
                  <MenuItem value="clothing">Clothing</MenuItem>
                  <MenuItem value="home">Home & Garden</MenuItem>
                  <MenuItem value="sports">Sports</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            
            <Grid item xs={12} md={2}>
              <FormControl fullWidth size="small">
                <InputLabel>Supplier</InputLabel>
                <Select
                  value={filters.supplier}
                  label="Supplier"
                  onChange={(e) => setFilters({ ...filters, supplier: e.target.value })}
                >
                  <MenuItem value="">All Suppliers</MenuItem>
                  {/* Populate with actual suppliers */}
                </Select>
              </FormControl>
            </Grid>
            
            <Grid item xs={12} md={2}>
              <FormControl fullWidth size="small">
                <InputLabel>Stock Level</InputLabel>
                <Select
                  value={filters.stockLevel}
                  label="Stock Level"
                  onChange={(e) => setFilters({ ...filters, stockLevel: e.target.value as any })}
                >
                  <MenuItem value="all">All Levels</MenuItem>
                  <MenuItem value="adequate">Adequate Stock</MenuItem>
                  <MenuItem value="low">Low Stock</MenuItem>
                  <MenuItem value="out">Out of Stock</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            
            <Grid item xs={12} md={3}>
              <Button
                variant="outlined"
                onClick={() => setFilters({
                  search: '',
                  category: '',
                  supplier: '',
                  status: '',
                  stockLevel: 'all'
                })}
                fullWidth
              >
                Clear Filters
              </Button>
            </Grid>
          </Grid>
        </CardContent>
      )}

      <CardContent sx={{ pt: 0 }}>
        <DataTable
          data={filteredProducts}
          columns={columns}
          loading={loading}
          selectable={true}
          selectedItems={selectedProducts}
          onSelectionChange={onSelectionChange}
          pagination={true}
          page={0}
          rowsPerPage={25}
          totalCount={filteredProducts.length}
          onPageChange={() => {}}
          onRowsPerPageChange={() => {}}
          emptyMessage="No products found"
        />
      </CardContent>
    </Card>
  );
};
```

### Supplier Directory Component
```typescript
// src/components/products/SupplierDirectory.tsx - Single Responsibility: Supplier management
import React, { useState } from 'react';
import {
  Card,
  CardHeader,
  CardContent,
  Typography,
  Box,
  Grid,
  Button,
  Avatar,
  Chip,
  Rating,
  LinearProgress,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  List,
  ListItem,
  ListItemText,
  ListItemAvatar
} from '@mui/material';
import {
  Business,
  Phone,
  Email,
  Language,
  Add,
  Edit,
  Visibility,
  Star,
  TrendingUp,
  Inventory2
} from '@mui/icons-material';
import { Supplier, SupplierPerformance } from '../../types';
import { formatCurrency, formatDate } from '../../utils/formatters';

interface SupplierDirectoryProps {
  suppliers: Supplier[];
  loading: boolean;
  onRefresh: () => void;
}

interface SupplierCardProps {
  supplier: Supplier;
  onEdit: (supplier: Supplier) => void;
  onView: (supplier: Supplier) => void;
}

const SupplierCard: React.FC<SupplierCardProps> = ({ supplier, onEdit, onView }) => {
  const getRatingColor = (rating: number): 'success' | 'warning' | 'error' => {
    if (rating >= 4) return 'success';
    if (rating >= 3) return 'warning';
    return 'error';
  };

  const getDeliveryRating = (days: number): 'success' | 'warning' | 'error' => {
    if (days <= 7) return 'success';
    if (days <= 14) return 'warning';
    return 'error';
  };

  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        {/* Header */}
        <Box sx={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Avatar sx={{ bgcolor: 'primary.main' }}>
              <Business />
            </Avatar>
            <Box>
              <Typography variant="h6" component="h3">
                {supplier.name}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {supplier.country}
              </Typography>
            </Box>
          </Box>
          
          <Box sx={{ display: 'flex', gap: 0.5 }}>
            <IconButton size="small" onClick={() => onView(supplier)}>
              <Visibility fontSize="small" />
            </IconButton>
            <IconButton size="small" onClick={() => onEdit(supplier)} color="primary">
              <Edit fontSize="small" />
            </IconButton>
          </Box>
        </Box>

        {/* Contact Info */}
        <Box sx={{ mb: 2 }}>
          <Typography variant="body2" sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
            <Email fontSize="small" color="action" />
            {supplier.contactEmail}
          </Typography>
          <Typography variant="body2" sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
            <Phone fontSize="small" color="action" />
            {supplier.contactPhone}
          </Typography>
          {supplier.website && (
            <Typography variant="body2" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Language fontSize="small" color="action" />
              <a href={supplier.website} target="_blank" rel="noopener noreferrer">
                Website
              </a>
            </Typography>
          )}
        </Box>

        {/* Performance Metrics */}
        <Box sx={{ mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
            <Typography variant="body2" color="text.secondary">
              Overall Rating
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
              <Rating
                value={supplier.performance.overallRating}
                readOnly
                size="small"
                precision={0.1}
              />
              <Typography variant="body2">
                ({supplier.performance.overallRating.toFixed(1)})
              </Typography>
            </Box>
          </Box>

          <Box sx={{ mb: 1 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
              <Typography variant="caption">
                Delivery Performance
              </Typography>
              <Typography variant="caption">
                {supplier.performance.averageDeliveryDays} days avg
              </Typography>
            </Box>
            <LinearProgress
              variant="determinate"
              value={Math.min(100, (14 - supplier.performance.averageDeliveryDays) * 10)}
              color={getDeliveryRating(supplier.performance.averageDeliveryDays)}
              sx={{ height: 6, borderRadius: 3 }}
            />
          </Box>

          <Box sx={{ mb: 1 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
              <Typography variant="caption">
                Quality Score
              </Typography>
              <Typography variant="caption">
                {supplier.performance.qualityScore.toFixed(1)}%
              </Typography>
            </Box>
            <LinearProgress
              variant="determinate"
              value={supplier.performance.qualityScore}
              color={getRatingColor(supplier.performance.qualityScore / 25)}
              sx={{ height: 6, borderRadius: 3 }}
            />
          </Box>
        </Box>

        {/* Stats */}
        <Grid container spacing={1} sx={{ mb: 2 }}>
          <Grid item xs={6}>
            <Box sx={{ textAlign: 'center', p: 1, bgcolor: 'background.paper', borderRadius: 1 }}>
              <Typography variant="h6" color="primary.main">
                {supplier.performance.totalProducts}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Products
              </Typography>
            </Box>
          </Grid>
          <Grid item xs={6}>
            <Box sx={{ textAlign: 'center', p: 1, bgcolor: 'background.paper', borderRadius: 1 }}>
              <Typography variant="h6" color="success.main">
                {formatCurrency(supplier.performance.totalPurchased)}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Purchased
              </Typography>
            </Box>
          </Grid>
        </Grid>

        {/* Tags/Categories */}
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
          {supplier.categories.map((category, index) => (
            <Chip
              key={index}
              label={category}
              size="small"
              variant="outlined"
              color="primary"
            />
          ))}
        </Box>
      </CardContent>
    </Card>
  );
};

export const SupplierDirectory: React.FC<SupplierDirectoryProps> = ({
  suppliers,
  loading,
  onRefresh
}) => {
  const [selectedSupplier, setSelectedSupplier] = useState<Supplier | null>(null);
  const [viewDialogOpen, setViewDialogOpen] = useState(false);

  const handleViewSupplier = (supplier: Supplier) => {
    setSelectedSupplier(supplier);
    setViewDialogOpen(true);
  };

  const handleEditSupplier = (supplier: Supplier) => {
    // Open edit supplier dialog
    console.log('Edit supplier:', supplier);
  };

  const topPerformers = suppliers
    .sort((a, b) => b.performance.overallRating - a.performance.overallRating)
    .slice(0, 3);

  return (
    <Box>
      {/* Top Performers Section */}
      <Card sx={{ mb: 3 }}>
        <CardHeader
          title="Top Performing Suppliers"
          subheader="Based on delivery time, quality, and overall satisfaction"
        />
        <CardContent>
          <Grid container spacing={2}>
            {topPerformers.map((supplier, index) => (
              <Grid item xs={12} md={4} key={supplier.id}>
                <Box sx={{ 
                  p: 2, 
                  border: 1, 
                  borderColor: index === 0 ? 'gold' : 'divider',
                  borderRadius: 1,
                  bgcolor: index === 0 ? 'warning.light' : 'transparent'
                }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                    {index === 0 && <Star sx={{ color: 'gold' }} />}
                    <Typography variant="subtitle1" fontWeight="medium">
                      {supplier.name}
                    </Typography>
                  </Box>
                  <Rating
                    value={supplier.performance.overallRating}
                    readOnly
                    size="small"
                    precision={0.1}
                  />
                  <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                    {supplier.performance.averageDeliveryDays} day avg delivery • {supplier.performance.totalProducts} products
                  </Typography>
                </Box>
              </Grid>
            ))}
          </Grid>
        </CardContent>
      </Card>

      {/* Supplier Grid */}
      <Card>
        <CardHeader
          title="All Suppliers"
          subheader={`${suppliers.length} suppliers in your network`}
          action={
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Button variant="outlined" onClick={onRefresh}>
                Refresh
              </Button>
              <Button
                variant="contained"
                startIcon={<Add />}
                onClick={() => {
                  // Open add supplier dialog
                }}
              >
                Add Supplier
              </Button>
            </Box>
          }
        />
        <CardContent>
          <Grid container spacing={2}>
            {suppliers.map((supplier) => (
              <Grid item xs={12} sm={6} lg={4} key={supplier.id}>
                <SupplierCard
                  supplier={supplier}
                  onEdit={handleEditSupplier}
                  onView={handleViewSupplier}
                />
              </Grid>
            ))}
          </Grid>
          
          {suppliers.length === 0 && !loading && (
            <Box sx={{ textAlign: 'center', py: 4 }}>
              <Typography variant="h6" color="text.secondary" gutterBottom>
                No suppliers found
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Start by adding your first supplier to track performance and manage relationships
              </Typography>
              <Button
                variant="contained"
                startIcon={<Add />}
                onClick={() => {
                  // Open add supplier dialog
                }}
              >
                Add First Supplier
              </Button>
            </Box>
          )}
        </CardContent>
      </Card>

      {/* View Supplier Dialog */}
      <Dialog
        open={viewDialogOpen}
        onClose={() => setViewDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        {selectedSupplier && (
          <>
            <DialogTitle>
              {selectedSupplier.name} - Supplier Details
            </DialogTitle>
            <DialogContent>
              <Grid container spacing={2}>
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2" gutterBottom>
                    Contact Information
                  </Typography>
                  <List dense>
                    <ListItem>
                      <ListItemAvatar>
                        <Avatar><Email /></Avatar>
                      </ListItemAvatar>
                      <ListItemText 
                        primary={selectedSupplier.contactEmail}
                        secondary="Email"
                      />
                    </ListItem>
                    <ListItem>
                      <ListItemAvatar>
                        <Avatar><Phone /></Avatar>
                      </ListItemAvatar>
                      <ListItemText 
                        primary={selectedSupplier.contactPhone}
                        secondary="Phone"
                      />
                    </ListItem>
                    {selectedSupplier.website && (
                      <ListItem>
                        <ListItemAvatar>
                          <Avatar><Language /></Avatar>
                        </ListItemAvatar>
                        <ListItemText 
                          primary={
                            <a href={selectedSupplier.website} target="_blank" rel="noopener noreferrer">
                              {selectedSupplier.website}
                            </a>
                          }
                          secondary="Website"
                        />
                      </ListItem>
                    )}
                  </List>
                </Grid>
                
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2" gutterBottom>
                    Performance Metrics
                  </Typography>
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="body2" gutterBottom>
                      Overall Rating: {selectedSupplier.performance.overallRating.toFixed(1)}/5
                    </Typography>
                    <Rating
                      value={selectedSupplier.performance.overallRating}
                      readOnly
                      precision={0.1}
                    />
                  </Box>
                  
                  <Typography variant="body2" gutterBottom>
                    Quality Score: {selectedSupplier.performance.qualityScore.toFixed(1)}%
                  </Typography>
                  <Typography variant="body2" gutterBottom>
                    Average Delivery: {selectedSupplier.performance.averageDeliveryDays} days
                  </Typography>
                  <Typography variant="body2" gutterBottom>
                    Total Products: {selectedSupplier.performance.totalProducts}
                  </Typography>
                  <Typography variant="body2" gutterBottom>
                    Total Purchased: {formatCurrency(selectedSupplier.performance.totalPurchased)}
                  </Typography>
                </Grid>
              </Grid>
            </DialogContent>
            <DialogActions>
              <Button onClick={() => setViewDialogOpen(false)}>
                Close
              </Button>
              <Button 
                variant="contained" 
                onClick={() => handleEditSupplier(selectedSupplier)}
              >
                Edit Supplier
              </Button>
            </DialogActions>
          </>
        )}
      </Dialog>
    </Box>
  );
};
```

## Implementation Tasks

### Task 1: Product Hub Foundation
1. **Create Product Hub Layout**
   - Implement tabbed interface with product/supplier/inventory/analytics tabs
   - Add quick stats dashboard with key metrics
   - Set up responsive layout for multi-device support

2. **Build Product Catalog Interface** 
   - Create product grid with comprehensive filtering
   - Add product-listing relationship indicators
   - Implement bulk product operations

3. **Test Product Hub Core**
   - Tab switching and data synchronization
   - Filtering performance with large datasets
   - Product-listing relationship accuracy

### Task 2: Supplier Directory
1. **Create Supplier Management**
   - Implement supplier card grid layout
   - Add supplier performance metrics display
   - Create supplier contact and relationship tracking

2. **Build Supplier Analytics**
   - Add top performer identification
   - Create supplier rating and quality scoring
   - Implement delivery performance tracking

3. **Test Supplier Features**
   - Supplier data accuracy and updates
   - Performance metric calculations
   - Contact information management

### Task 3: Inventory Management
1. **Implement Inventory Dashboard**
   - Create stock level monitoring interface
   - Add low stock and out-of-stock alerts
   - Implement inventory movement tracking

2. **Build Reorder Management**
   - Create intelligent reorder point calculations
   - Add reorder recommendation system
   - Implement bulk reorder processing

3. **Test Inventory Functions**
   - Stock level accuracy and real-time updates
   - Reorder point calculations
   - Alert system functionality

### Task 4: Integration & Analytics
1. **Product-Supplier Integration**
   - Connect product catalog with supplier data
   - Implement cross-reference linking
   - Add relationship management tools

2. **Analytics & Reporting**
   - Create comprehensive product/supplier analytics
   - Add performance trend analysis
   - Implement profit margin tracking

3. **Test Integration**
   - Data consistency across modules
   - Analytics accuracy and performance
   - Cross-module navigation and synchronization

### Task 5: Advanced Features
1. **Smart Recommendations**
   - Implement product sourcing suggestions
   - Add supplier recommendation engine
   - Create automated reorder workflows

2. **Export & Import**
   - Add CSV export for products and suppliers
   - Implement bulk product import functionality
   - Create data backup and restore features

3. **Test Advanced Features**
   - Recommendation accuracy
   - Import/export functionality
   - Performance with complex operations

## Quality Gates

### Performance Requirements
- [ ] Product catalog loading: <1 second for 1000 products
- [ ] Supplier directory: <500ms for 100 suppliers 
- [ ] Inventory calculations: Real-time updates
- [ ] Analytics generation: <3 seconds for complex metrics
- [ ] Memory usage: <100MB for full product dataset

### Functionality Requirements
- [ ] Product-supplier relationships accurately tracked
- [ ] Inventory levels update in real-time
- [ ] Reorder recommendations are accurate
- [ ] Supplier performance metrics calculate correctly
- [ ] Cross-module data synchronization works properly

### SOLID Compliance Checklist
- [ ] Each component has single responsibility
- [ ] Product import system is extensible
- [ ] Supplier data sources are interchangeable
- [ ] Inventory interfaces are properly segregated
- [ ] All services depend on abstractions

---
**Next Phase**: Communication Center with unified inbox and message classification.