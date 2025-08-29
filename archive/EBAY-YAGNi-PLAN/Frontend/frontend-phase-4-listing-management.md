# Frontend Phase 4: Listing Management Interface Implementation

## Overview
Implement dual-pane listing management interface with Active Listings (from eBay CSV) and Draft Listings (preparation workflow). Includes performance analytics, bulk operations, and seamless transition from draft to active listings.

## SOLID/YAGNI Compliance Strategy

### Single Responsibility Principle (SRP)
- **ActiveListingsPanel**: Only handle active eBay listings display and management
- **DraftListingsPanel**: Only manage draft listing preparation workflow
- **ListingDetail**: Only show individual listing information and editing
- **BulkListingActions**: Only handle multi-listing operations
- **PerformanceAnalytics**: Only calculate and display listing performance metrics
- **CompletionTracker**: Only track draft listing completion progress

### Open/Closed Principle (OCP)
- **Listing Status Workflows**: Extensible status transitions without core changes
- **Performance Metrics**: Add new analytics without modifying existing calculations
- **Export Formats**: Support multiple export formats through strategy pattern
- **Validation Rules**: Add new listing validation rules through configuration

### Liskov Substitution Principle (LSP)
- **Listing Providers**: Active and draft listing sources interchangeable
- **Analytics Calculators**: Different metric calculators substitutable
- **Status Handlers**: All status update handlers follow same interface

### Interface Segregation Principle (ISP)
- **Listing Interfaces**: Separate read-only vs editable listing operations
- **Analytics Interfaces**: Different interfaces for simple vs complex metrics
- **Action Interfaces**: Segregate individual vs bulk listing operations

### Dependency Inversion Principle (DIP)
- **Listing Services**: Components depend on abstract listing interfaces
- **Data Sources**: Configurable CSV and API data providers
- **Analytics Services**: Pluggable performance calculation engines

## Listing Management Architecture

### Main Listing Management Layout
```typescript
// src/components/listings/ListingManagement.tsx - Single Responsibility: Listing interface composition
import React, { useState, useMemo } from 'react';
import { 
  Box, 
  Container, 
  Paper, 
  Tabs, 
  Tab, 
  Grid,
  Switch,
  FormControlLabel
} from '@mui/material';
import { ListingHeader } from './ListingHeader';
import { ActiveListingsPanel } from './ActiveListingsPanel';
import { DraftListingsPanel } from './DraftListingsPanel';
import { ListingAnalytics } from './ListingAnalytics';
import { ListingFilters } from './ListingFilters';
import { BulkActionBar } from './BulkActionBar';
import { useListingData } from '../../hooks/useListingData';
import { useListingFilters } from '../../hooks/useListingFilters';

type ListingTab = 'active' | 'draft' | 'analytics';

export const ListingManagement: React.FC = () => {
  const [activeTab, setActiveTab] = useState<ListingTab>('active');
  const [selectedListings, setSelectedListings] = useState<string[]>([]);
  const [splitView, setSplitView] = useState(false);

  const { filters, updateFilter, resetFilters } = useListingFilters();
  const { 
    activeListings, 
    draftListings, 
    analytics,
    loading, 
    refresh 
  } = useListingData(filters);

  const handleTabChange = (_: React.SyntheticEvent, newValue: ListingTab) => {
    setActiveTab(newValue);
    setSelectedListings([]); // Clear selection when switching tabs
  };

  const handleBulkAction = async (action: string, listingIds: string[]) => {
    // Handle bulk operations for both active and draft listings
    await performBulkAction(action, listingIds, activeTab);
    setSelectedListings([]);
    refresh();
  };

  return (
    <Container maxWidth="xl" sx={{ py: 3 }}>
      {/* Header with listing metrics */}
      <ListingHeader 
        activeCount={activeListings.length}
        draftCount={draftListings.length}
        onRefresh={refresh}
        loading={loading}
      />

      {/* Tab Navigation and View Controls */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 2 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Tabs value={activeTab} onChange={handleTabChange}>
            <Tab 
              label={`Active Listings (${activeListings.length})`} 
              value="active" 
            />
            <Tab 
              label={`Draft Listings (${draftListings.length})`} 
              value="draft" 
            />
            <Tab 
              label="Performance Analytics" 
              value="analytics" 
            />
          </Tabs>
          
          {activeTab !== 'analytics' && (
            <FormControlLabel
              control={
                <Switch
                  checked={splitView}
                  onChange={(e) => setSplitView(e.target.checked)}
                />
              }
              label="Split View"
            />
          )}
        </Box>
      </Box>

      {/* Filters */}
      <Paper sx={{ p: 2, mb: 2 }}>
        <ListingFilters
          filters={filters}
          onFilterChange={updateFilter}
          onReset={resetFilters}
          listingType={activeTab}
        />
      </Paper>

      {/* Bulk Action Bar */}
      {selectedListings.length > 0 && activeTab !== 'analytics' && (
        <BulkActionBar
          selectedCount={selectedListings.length}
          listingType={activeTab}
          onBulkAction={(action) => handleBulkAction(action, selectedListings)}
          onCancel={() => setSelectedListings([])}
        />
      )}

      {/* Main Content */}
      {splitView && activeTab !== 'analytics' ? (
        // Split view: Active and Draft side by side
        <Grid container spacing={2}>
          <Grid item xs={6}>
            <ActiveListingsPanel
              listings={activeListings}
              loading={loading}
              selectedListings={selectedListings}
              onSelectionChange={setSelectedListings}
              filters={filters}
            />
          </Grid>
          <Grid item xs={6}>
            <DraftListingsPanel
              listings={draftListings}
              loading={loading}
              selectedListings={selectedListings}
              onSelectionChange={setSelectedListings}
              filters={filters}
            />
          </Grid>
        </Grid>
      ) : (
        // Single view
        <Box>
          {activeTab === 'active' && (
            <ActiveListingsPanel
              listings={activeListings}
              loading={loading}
              selectedListings={selectedListings}
              onSelectionChange={setSelectedListings}
              filters={filters}
            />
          )}
          
          {activeTab === 'draft' && (
            <DraftListingsPanel
              listings={draftListings}
              loading={loading}
              selectedListings={selectedListings}
              onSelectionChange={setSelectedListings}
              filters={filters}
            />
          )}
          
          {activeTab === 'analytics' && (
            <ListingAnalytics
              data={analytics}
              loading={loading}
            />
          )}
        </Box>
      )}
    </Container>
  );
};
```

### Active Listings Panel
```typescript
// src/components/listings/ActiveListingsPanel.tsx - Single Responsibility: Active listings display
import React from 'react';
import {
  Card,
  CardHeader,
  CardContent,
  Typography,
  Box,
  Chip,
  IconButton,
  Avatar
} from '@mui/material';
import {
  Visibility,
  Edit,
  Pause,
  PlayArrow,
  TrendingUp,
  TrendingDown,
  RemoveRedEye
} from '@mui/icons-material';
import { DataTable, TableColumn } from '../common/DataTable';
import { StatusBadge } from '../common/StatusBadge';
import { EbayListing, ListingFilter } from '../../types';
import { formatCurrency, formatDate } from '../../utils/formatters';

interface ActiveListingsPanelProps {
  listings: EbayListing[];
  loading: boolean;
  selectedListings: string[];
  onSelectionChange: (listingIds: string[]) => void;
  filters: ListingFilter;
}

export const ActiveListingsPanel: React.FC<ActiveListingsPanelProps> = ({
  listings,
  loading,
  selectedListings,
  onSelectionChange,
  filters
}) => {
  const columns: TableColumn<EbayListing>[] = [
    {
      id: 'image',
      label: '',
      accessor: (listing) => (
        <Avatar
          src={listing.primaryImageUrl}
          variant="rounded"
          sx={{ width: 48, height: 48 }}
        />
      ),
      width: 60
    },
    {
      id: 'title',
      label: 'Listing',
      accessor: (listing) => (
        <Box>
          <Typography variant="body2" fontWeight="medium" noWrap>
            {listing.title}
          </Typography>
          <Typography variant="caption" color="text.secondary">
            SKU: {listing.sku} • Item: {listing.ebayItemId}
          </Typography>
        </Box>
      ),
      width: 300
    },
    {
      id: 'price',
      label: 'Price',
      accessor: (listing) => (
        <Typography variant="body2" fontWeight="medium">
          {formatCurrency(listing.currentPrice)}
        </Typography>
      ),
      width: 100,
      align: 'right'
    },
    {
      id: 'inventory',
      label: 'Inventory',
      accessor: (listing) => (
        <Box>
          <Typography variant="body2">
            {listing.quantityAvailable} available
          </Typography>
          <Typography variant="caption" color="text.secondary">
            {listing.quantitySold} sold
          </Typography>
        </Box>
      ),
      width: 120
    },
    {
      id: 'performance',
      label: 'Performance',
      accessor: (listing) => (
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Chip
            icon={<RemoveRedEye />}
            label={listing.performance.viewCount}
            size="small"
            variant="outlined"
          />
          <Chip
            label={`${listing.watchers} watching`}
            size="small"
            variant="outlined"
            color={listing.watchers > 5 ? 'success' : 'default'}
          />
        </Box>
      ),
      width: 180
    },
    {
      id: 'status',
      label: 'Status',
      accessor: (listing) => (
        <StatusBadge status={listing.status} />
      ),
      width: 100
    },
    {
      id: 'dates',
      label: 'Duration',
      accessor: (listing) => (
        <Box>
          <Typography variant="caption" display="block">
            Started: {formatDate(listing.startDate)}
          </Typography>
          <Typography variant="caption" color="text.secondary">
            Ends: {formatDate(listing.endDate)}
          </Typography>
        </Box>
      ),
      width: 140
    },
    {
      id: 'actions',
      label: 'Actions',
      accessor: (listing) => (
        <Box sx={{ display: 'flex', gap: 0.5 }}>
          <IconButton
            size="small"
            onClick={(e) => {
              e.stopPropagation();
              // View listing details
            }}
            title="View Details"
          >
            <Visibility fontSize="small" />
          </IconButton>
          
          <IconButton
            size="small"
            onClick={(e) => {
              e.stopPropagation();
              // Edit listing
            }}
            title="Edit Listing"
            color="primary"
          >
            <Edit fontSize="small" />
          </IconButton>
          
          {listing.status === 'active' ? (
            <IconButton
              size="small"
              onClick={(e) => {
                e.stopPropagation();
                // Pause listing
              }}
              title="Pause Listing"
              color="warning"
            >
              <Pause fontSize="small" />
            </IconButton>
          ) : (
            <IconButton
              size="small"
              onClick={(e) => {
                e.stopPropagation();
                // Activate listing
              }}
              title="Activate Listing"
              color="success"
            >
              <PlayArrow fontSize="small" />
            </IconButton>
          )}
        </Box>
      ),
      width: 120
    }
  ];

  return (
    <Card>
      <CardHeader
        title="Active Listings"
        subheader={`${listings.length} listings from eBay CSV data`}
      />
      <CardContent sx={{ pt: 0 }}>
        <DataTable
          data={listings}
          columns={columns}
          loading={loading}
          selectable={true}
          selectedItems={selectedListings}
          onSelectionChange={onSelectionChange}
          pagination={true}
          page={0}
          rowsPerPage={25}
          totalCount={listings.length}
          onPageChange={() => {}}
          onRowsPerPageChange={() => {}}
          emptyMessage="No active listings found"
        />
      </CardContent>
    </Card>
  );
};
```

### Draft Listings Panel
```typescript
// src/components/listings/DraftListingsPanel.tsx - Single Responsibility: Draft listings workflow
import React from 'react';
import {
  Card,
  CardHeader,
  CardContent,
  Typography,
  Box,
  LinearProgress,
  Chip,
  IconButton,
  Button
} from '@mui/material';
import {
  Edit,
  Publish,
  Delete,
  CheckCircle,
  Warning,
  Schedule
} from '@mui/icons-material';
import { DataTable, TableColumn } from '../common/DataTable';
import { StatusBadge } from '../common/StatusBadge';
import { DraftListing, ListingFilter } from '../../types';
import { formatCurrency, formatDate } from '../../utils/formatters';

interface DraftListingsPanelProps {
  listings: DraftListing[];
  loading: boolean;
  selectedListings: string[];
  onSelectionChange: (listingIds: string[]) => void;
  filters: ListingFilter;
}

export const DraftListingsPanel: React.FC<DraftListingsPanelProps> = ({
  listings,
  loading,
  selectedListings,
  onSelectionChange,
  filters
}) => {
  const getCompletionColor = (percentage: number): 'success' | 'warning' | 'error' => {
    if (percentage >= 90) return 'success';
    if (percentage >= 60) return 'warning';
    return 'error';
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'complete': return <CheckCircle color="success" />;
      case 'pending_review': return <Warning color="warning" />;
      case 'incomplete': return <Schedule color="error" />;
      default: return <Schedule />;
    }
  };

  const columns: TableColumn<DraftListing>[] = [
    {
      id: 'title',
      label: 'Draft Listing',
      accessor: (draft) => (
        <Box>
          <Typography variant="body2" fontWeight="medium">
            {draft.title || 'Untitled Draft'}
          </Typography>
          <Typography variant="caption" color="text.secondary">
            SKU: {draft.sku}
          </Typography>
        </Box>
      ),
      width: 250
    },
    {
      id: 'completion',
      label: 'Completion',
      accessor: (draft) => (
        <Box sx={{ width: '100%' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 0.5 }}>
            <Typography variant="body2" sx={{ mr: 1 }}>
              {draft.completionPercentage}%
            </Typography>
            {getStatusIcon(draft.listingStatus)}
          </Box>
          <LinearProgress
            variant="determinate"
            value={draft.completionPercentage}
            color={getCompletionColor(draft.completionPercentage)}
            sx={{ height: 6, borderRadius: 3 }}
          />
        </Box>
      ),
      width: 150
    },
    {
      id: 'status',
      label: 'Status',
      accessor: (draft) => (
        <StatusBadge status={draft.listingStatus} />
      ),
      width: 120
    },
    {
      id: 'price',
      label: 'Price',
      accessor: (draft) => (
        <Box>
          <Typography variant="body2" fontWeight="medium">
            {formatCurrency(draft.price)}
          </Typography>
          <Typography variant="caption" color="success.main">
            Est. Profit: {formatCurrency(draft.estimatedProfit)}
          </Typography>
        </Box>
      ),
      width: 120,
      align: 'right'
    },
    {
      id: 'images',
      label: 'Images',
      accessor: (draft) => (
        <Chip
          label={`${draft.imagesUploaded}/10`}
          size="small"
          color={draft.imagesUploaded >= 5 ? 'success' : 'warning'}
          variant="outlined"
        />
      ),
      width: 80
    },
    {
      id: 'modified',
      label: 'Last Modified',
      accessor: (draft) => formatDate(draft.lastModified),
      width: 120
    },
    {
      id: 'notes',
      label: 'Notes',
      accessor: (draft) => (
        <Typography
          variant="caption"
          color="text.secondary"
          sx={{
            maxWidth: 200,
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap'
          }}
        >
          {draft.notes || 'No notes'}
        </Typography>
      ),
      width: 200
    },
    {
      id: 'actions',
      label: 'Actions',
      accessor: (draft) => (
        <Box sx={{ display: 'flex', gap: 0.5 }}>
          <IconButton
            size="small"
            onClick={(e) => {
              e.stopPropagation();
              // Edit draft
            }}
            title="Edit Draft"
            color="primary"
          >
            <Edit fontSize="small" />
          </IconButton>
          
          {draft.completionPercentage >= 90 && (
            <IconButton
              size="small"
              onClick={(e) => {
                e.stopPropagation();
                // Publish to eBay
              }}
              title="Publish to eBay"
              color="success"
            >
              <Publish fontSize="small" />
            </IconButton>
          )}
          
          <IconButton
            size="small"
            onClick={(e) => {
              e.stopPropagation();
              // Delete draft
            }}
            title="Delete Draft"
            color="error"
          >
            <Delete fontSize="small" />
          </IconButton>
        </Box>
      ),
      width: 120
    }
  ];

  const readyToPublishCount = listings.filter(draft => draft.completionPercentage >= 90).length;

  return (
    <Card>
      <CardHeader
        title="Draft Listings"
        subheader={`${listings.length} drafts • ${readyToPublishCount} ready to publish`}
        action={
          readyToPublishCount > 0 && (
            <Button
              variant="contained"
              color="success"
              startIcon={<Publish />}
              onClick={() => {
                // Bulk publish ready drafts
              }}
            >
              Publish {readyToPublishCount} Ready
            </Button>
          )
        }
      />
      <CardContent sx={{ pt: 0 }}>
        <DataTable
          data={listings}
          columns={columns}
          loading={loading}
          selectable={true}
          selectedItems={selectedListings}
          onSelectionChange={onSelectionChange}
          pagination={true}
          page={0}
          rowsPerPage={25}
          totalCount={listings.length}
          onPageChange={() => {}}
          onRowsPerPageChange={() => {}}
          emptyMessage="No draft listings found"
        />
      </CardContent>
    </Card>
  );
};
```

### Listing Performance Analytics
```typescript
// src/components/listings/ListingAnalytics.tsx - Single Responsibility: Performance analytics
import React, { useState } from 'react';
import {
  Grid,
  Card,
  CardHeader,
  CardContent,
  Typography,
  Box,
  ToggleButtonGroup,
  ToggleButton,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Chip
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  RemoveRedEye,
  ShoppingCart,
  AttachMoney,
  Schedule
} from '@mui/icons-material';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line
} from 'recharts';
import { useTheme } from '@mui/material/styles';

interface ListingAnalyticsData {
  overview: {
    totalListings: number;
    activeListings: number;
    soldListings: number;
    averagePrice: number;
    totalViews: number;
    conversionRate: number;
  };
  performanceChart: Array<{
    date: string;
    views: number;
    sales: number;
    revenue: number;
  }>;
  topPerformers: Array<{
    id: string;
    title: string;
    views: number;
    sales: number;
    revenue: number;
    conversionRate: number;
  }>;
  categoryBreakdown: Array<{
    category: string;
    count: number;
    revenue: number;
  }>;
}

interface ListingAnalyticsProps {
  data: ListingAnalyticsData;
  loading: boolean;
}

export const ListingAnalytics: React.FC<ListingAnalyticsProps> = ({
  data,
  loading
}) => {
  const theme = useTheme();
  const [timeRange, setTimeRange] = useState<'7d' | '30d' | '90d'>('30d');

  if (loading) {
    return (
      <Box sx={{ p: 3, textAlign: 'center' }}>
        <Typography>Loading analytics...</Typography>
      </Box>
    );
  }

  const overviewCards = [
    {
      title: 'Total Listings',
      value: data.overview.totalListings,
      icon: <Schedule />,
      color: 'primary' as const
    },
    {
      title: 'Active Listings',
      value: data.overview.activeListings,
      icon: <TrendingUp />,
      color: 'success' as const
    },
    {
      title: 'Total Views',
      value: data.overview.totalViews.toLocaleString(),
      icon: <RemoveRedEye />,
      color: 'info' as const
    },
    {
      title: 'Conversion Rate',
      value: `${data.overview.conversionRate.toFixed(1)}%`,
      icon: <ShoppingCart />,
      color: 'warning' as const
    }
  ];

  const COLORS = [theme.palette.primary.main, theme.palette.success.main, theme.palette.warning.main, theme.palette.error.main];

  return (
    <Box>
      {/* Time Range Selector */}
      <Box sx={{ mb: 3, display: 'flex', justifyContent: 'flex-end' }}>
        <ToggleButtonGroup
          value={timeRange}
          exclusive
          onChange={(_, newRange) => newRange && setTimeRange(newRange)}
          size="small"
        >
          <ToggleButton value="7d">7 Days</ToggleButton>
          <ToggleButton value="30d">30 Days</ToggleButton>
          <ToggleButton value="90d">90 Days</ToggleButton>
        </ToggleButtonGroup>
      </Box>

      {/* Overview Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        {overviewCards.map((card, index) => (
          <Grid item xs={12} sm={6} md={3} key={index}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <Box>
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      {card.title}
                    </Typography>
                    <Typography variant="h4" component="div">
                      {card.value}
                    </Typography>
                  </Box>
                  <Box sx={{ 
                    p: 1, 
                    borderRadius: 1, 
                    bgcolor: `${card.color}.light`,
                    color: `${card.color}.main`
                  }}>
                    {card.icon}
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      <Grid container spacing={3}>
        {/* Performance Chart */}
        <Grid item xs={12} lg={8}>
          <Card>
            <CardHeader title="Performance Trends" />
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={data.performanceChart}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip />
                  <Line 
                    type="monotone" 
                    dataKey="views" 
                    stroke={theme.palette.primary.main}
                    name="Views"
                  />
                  <Line 
                    type="monotone" 
                    dataKey="sales" 
                    stroke={theme.palette.success.main}
                    name="Sales"
                  />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Category Breakdown */}
        <Grid item xs={12} lg={4}>
          <Card>
            <CardHeader title="Category Breakdown" />
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={data.categoryBreakdown}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="count"
                    label={({ category, percent }) => `${category} ${(percent * 100).toFixed(0)}%`}
                  >
                    {data.categoryBreakdown.map((_, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Top Performers Table */}
        <Grid item xs={12}>
          <Card>
            <CardHeader title="Top Performing Listings" />
            <CardContent>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Listing Title</TableCell>
                    <TableCell align="right">Views</TableCell>
                    <TableCell align="right">Sales</TableCell>
                    <TableCell align="right">Revenue</TableCell>
                    <TableCell align="right">Conversion Rate</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {data.topPerformers.slice(0, 10).map((listing) => (
                    <TableRow key={listing.id}>
                      <TableCell>
                        <Typography variant="body2" noWrap sx={{ maxWidth: 300 }}>
                          {listing.title}
                        </Typography>
                      </TableCell>
                      <TableCell align="right">
                        {listing.views.toLocaleString()}
                      </TableCell>
                      <TableCell align="right">
                        {listing.sales}
                      </TableCell>
                      <TableCell align="right">
                        ${listing.revenue.toLocaleString()}
                      </TableCell>
                      <TableCell align="right">
                        <Chip
                          label={`${listing.conversionRate.toFixed(1)}%`}
                          size="small"
                          color={listing.conversionRate > 5 ? 'success' : listing.conversionRate > 2 ? 'warning' : 'default'}
                        />
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};
```

## Implementation Tasks

### Task 1: Dual-Pane Layout Implementation
1. **Create Listing Management Container**
   - Implement tabbed interface with active/draft/analytics tabs
   - Add split-view toggle for side-by-side comparison
   - Set up responsive layout for mobile/tablet

2. **Build Active Listings Panel**
   - Integrate with eBay CSV data structure
   - Add performance indicators and status management
   - Implement inline editing capabilities

3. **Test Layout Functionality**
   - Tab switching and state management
   - Split-view responsive behavior
   - Data synchronization between panels

### Task 2: Draft Listing Workflow
1. **Create Draft Listing Panel**
   - Implement completion percentage tracking
   - Add draft status workflow management
   - Create publish-to-eBay functionality

2. **Build Draft Editor**
   - Create comprehensive listing creation form
   - Add image upload and management
   - Implement draft auto-save functionality

3. **Test Draft Workflow**
   - Draft creation and editing flow
   - Completion percentage accuracy
   - Publish workflow integration

### Task 3: Performance Analytics
1. **Implement Analytics Dashboard**
   - Create performance charts and metrics
   - Add top performers and category breakdowns
   - Build conversion rate tracking

2. **Add Analytics Filters**
   - Time range selection functionality
   - Category and performance filtering
   - Export analytics reports

3. **Test Analytics Features**
   - Data accuracy and calculation correctness
   - Chart rendering and interactivity
   - Performance with large datasets

### Task 4: Bulk Operations
1. **Create Bulk Action System**
   - Implement multi-listing selection
   - Add bulk status updates and pricing changes
   - Create bulk publish functionality

2. **Add Advanced Bulk Operations**
   - Bulk image management
   - Bulk description updates
   - Bulk category changes

3. **Test Bulk Operations**
   - Multi-selection accuracy
   - Bulk operation performance
   - Error handling during bulk updates

### Task 5: Integration Points
1. **CSV Data Integration**
   - Connect with eBay CSV import system
   - Add real-time data synchronization
   - Implement data validation and error handling

2. **Product Catalog Integration**
   - Link listings to product database
   - Add inventory level synchronization
   - Create supplier information display

3. **Test Integration**
   - CSV data import accuracy
   - Product catalog synchronization
   - Cross-module data consistency

## Quality Gates

### Performance Requirements
- [ ] Listing table loading: <800ms for 1000 listings
- [ ] Draft completion tracking: Real-time updates
- [ ] Analytics calculation: <2 seconds for complex metrics
- [ ] Bulk operations: <10 seconds for 100 listings
- [ ] Memory usage: <80MB for full listing dataset

### Functionality Requirements
- [ ] Active listings display eBay CSV data accurately
- [ ] Draft completion tracking works correctly
- [ ] Performance analytics show accurate metrics
- [ ] Bulk operations handle errors gracefully
- [ ] Split-view synchronizes data properly

### SOLID Compliance Checklist
- [ ] Each panel has single responsibility
- [ ] Analytics system is extensible
- [ ] Listing providers are interchangeable
- [ ] Bulk operations follow consistent interface
- [ ] All dependencies properly injected

---
**Next Phase**: Product & Supplier Hub with relationship management and inventory tracking.