# Frontend Phase 2: Multi-Account Dashboard Implementation

## Overview
Implement comprehensive multi-account dashboard with KPI cards, performance charts, and real-time updates. Central command center for managing 30 eBay accounts with account switching and health monitoring.

## SOLID/YAGNI Compliance Strategy

### Single Responsibility Principle (SRP)
- **KPICard**: Only display one metric with trend visualization
- **AccountSwitcher**: Only handle account selection and health display
- **PerformanceChart**: Only render chart data and interactions
- **QuickActionHub**: Only manage common operation shortcuts
- **ActivityFeed**: Only display recent account activities

### Open/Closed Principle (OCP)
- **Widget System**: Add new dashboard widgets without modifying existing ones
- **Chart Types**: Support multiple chart libraries through common interface
- **KPI Metrics**: Extensible metric calculations through plugin system
- **Action Providers**: Add new quick actions through configuration

### Liskov Substitution Principle (LSP)
- **Chart Implementations**: All chart components follow same data interface
- **Widget Providers**: All dashboard widgets interchangeable
- **Data Sources**: Real-time and cached data sources substitutable

### Interface Segregation Principle (ISP)
- **Dashboard Interfaces**: Separate read-only vs interactive widgets
- **Account Interfaces**: Segregate account data vs account operations
- **Chart Interfaces**: Different interfaces for simple vs complex charts

### Dependency Inversion Principle (DIP)
- **Data Services**: Dashboard depends on abstract data interfaces
- **Widget Configuration**: Configurable widget composition
- **Update Mechanisms**: Pluggable real-time update strategies

## Dashboard Architecture

### Main Dashboard Layout
```typescript
// src/components/dashboard/Dashboard.tsx - Single Responsibility: Dashboard composition
import React from 'react';
import { Grid, Container, Box } from '@mui/material';
import { AccountSwitcher } from './AccountSwitcher';
import { DashboardHeader } from './DashboardHeader';
import { KPISection } from './KPISection';
import { PerformanceChart } from './PerformanceChart';
import { QuickActionHub } from './QuickActionHub';
import { ActivityFeed } from './ActivityFeed';
import { useAccountStore } from '../../store/accountStore';
import { useDashboardData } from '../../hooks/useDashboardData';

export const Dashboard: React.FC = () => {
  const { currentAccount } = useAccountStore();
  const { dashboardData, loading, error, refresh } = useDashboardData(currentAccount?.id);

  if (!currentAccount) {
    return <AccountSelection />; // Redirect to account selection
  }

  return (
    <Container maxWidth="xl" sx={{ py: 3 }}>
      {/* Header with Account Switcher */}
      <DashboardHeader 
        account={currentAccount}
        onRefresh={refresh}
        loading={loading}
      />

      {/* KPI Cards Row */}
      <KPISection 
        metrics={dashboardData?.metrics}
        loading={loading}
      />

      {/* Main Content Grid */}
      <Grid container spacing={3} sx={{ mt: 2 }}>
        {/* Performance Chart */}
        <Grid item xs={12} lg={8}>
          <PerformanceChart 
            data={dashboardData?.performanceData}
            loading={loading}
          />
        </Grid>
        
        {/* Quick Actions & Activity */}
        <Grid item xs={12} lg={4}>
          <Grid container spacing={2}>
            <Grid item xs={12}>
              <QuickActionHub accountId={currentAccount.id} />
            </Grid>
            <Grid item xs={12}>
              <ActivityFeed 
                activities={dashboardData?.recentActivities}
                loading={loading}
              />
            </Grid>
          </Grid>
        </Grid>
      </Grid>
    </Container>
  );
};
```

### Account Switcher Component
```typescript
// src/components/dashboard/AccountSwitcher.tsx - Single Responsibility: Account selection
import React, { useState } from 'react';
import {
  Box,
  Button,
  Menu,
  MenuItem,
  Typography,
  Avatar,
  Chip,
  ListItemIcon,
  ListItemText,
  Divider
} from '@mui/material';
import {
  ExpandMore,
  Store,
  CheckCircle,
  Warning,
  Error,
  Sync
} from '@mui/icons-material';
import { EbayAccount } from '../../types';
import { useAccountStore } from '../../store/accountStore';
import { useAccountService } from '../../hooks/useAccountService';

interface AccountSwitcherProps {
  currentAccount: EbayAccount;
  onAccountChange?: (account: EbayAccount) => void;
}

export const AccountSwitcher: React.FC<AccountSwitcherProps> = ({
  currentAccount,
  onAccountChange
}) => {
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const { accounts, setCurrentAccount } = useAccountStore();
  const { syncAccount } = useAccountService();
  
  const handleClick = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  const handleAccountSelect = async (account: EbayAccount) => {
    setCurrentAccount(account);
    onAccountChange?.(account);
    handleClose();
  };

  const handleSyncAccount = async (accountId: string, event: React.MouseEvent) => {
    event.stopPropagation();
    await syncAccount(accountId);
  };

  const getHealthIcon = (health: string) => {
    switch (health) {
      case 'good': return <CheckCircle sx={{ color: 'success.main' }} />;
      case 'warning': return <Warning sx={{ color: 'warning.main' }} />;
      case 'critical': return <Error sx={{ color: 'error.main' }} />;
      default: return <Store />;
    }
  };

  const getHealthColor = (health: string): 'success' | 'warning' | 'error' | 'default' => {
    switch (health) {
      case 'good': return 'success';
      case 'warning': return 'warning';  
      case 'critical': return 'error';
      default: return 'default';
    }
  };

  return (
    <Box>
      <Button
        variant="outlined"
        onClick={handleClick}
        endIcon={<ExpandMore />}
        startIcon={getHealthIcon(currentAccount.health)}
        sx={{ 
          minWidth: 300,
          justifyContent: 'space-between',
          px: 2,
          py: 1
        }}
      >
        <Box sx={{ textAlign: 'left', flex: 1 }}>
          <Typography variant="subtitle1" noWrap>
            {currentAccount.displayName}
          </Typography>
          <Typography variant="body2" color="text.secondary" noWrap>
            @{currentAccount.username}
          </Typography>
        </Box>
        <Chip 
          label={currentAccount.health.toUpperCase()}
          size="small"
          color={getHealthColor(currentAccount.health)}
        />
      </Button>

      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleClose}
        PaperProps={{
          sx: { width: 350, maxHeight: 400 }
        }}
      >
        <Typography variant="overline" sx={{ px: 2, py: 1, color: 'text.secondary' }}>
          Select Account ({accounts.length})
        </Typography>
        <Divider />
        
        {accounts.map((account) => (
          <MenuItem
            key={account.id}
            onClick={() => handleAccountSelect(account)}
            selected={account.id === currentAccount.id}
            sx={{ py: 1.5 }}
          >
            <ListItemIcon>
              {getHealthIcon(account.health)}
            </ListItemIcon>
            
            <ListItemText
              primary={account.displayName}
              secondary={
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    @{account.username}
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 1, mt: 0.5 }}>
                    <Typography variant="caption">
                      {account.metrics.totalOrders} orders
                    </Typography>
                    <Typography variant="caption">
                      ${account.metrics.totalRevenue.toLocaleString()}
                    </Typography>
                  </Box>
                </Box>
              }
            />
            
            <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 0.5 }}>
              <Chip 
                label={account.health}
                size="small"
                color={getHealthColor(account.health)}
              />
              <Button
                size="small"
                startIcon={<Sync />}
                onClick={(e) => handleSyncAccount(account.id, e)}
                sx={{ fontSize: '0.7rem' }}
              >
                Sync
              </Button>
            </Box>
          </MenuItem>
        ))}
      </Menu>
    </Box>
  );
};
```

### KPI Section Component
```typescript
// src/components/dashboard/KPISection.tsx - Single Responsibility: KPI display
import React from 'react';
import { Grid, Skeleton } from '@mui/material';
import { KPICard } from './KPICard';
import { AccountMetrics } from '../../types';

interface KPISectionProps {
  metrics?: AccountMetrics;
  loading: boolean;
}

export const KPISection: React.FC<KPISectionProps> = ({ metrics, loading }) => {
  if (loading) {
    return (
      <Grid container spacing={3} sx={{ mb: 3 }}>
        {[1, 2, 3, 4].map((i) => (
          <Grid item xs={12} sm={6} lg={3} key={i}>
            <Skeleton variant="rectangular" height={120} />
          </Grid>
        ))}
      </Grid>
    );
  }

  if (!metrics) {
    return null;
  }

  return (
    <Grid container spacing={3} sx={{ mb: 3 }}>
      <Grid item xs={12} sm={6} lg={3}>
        <KPICard
          title="Total Orders"
          value={metrics.totalOrders}
          trend={metrics.ordersTrend}
          icon="orders"
          color="primary"
        />
      </Grid>
      
      <Grid item xs={12} sm={6} lg={3}>
        <KPICard
          title="Revenue"
          value={`$${metrics.totalRevenue.toLocaleString()}`}
          trend={metrics.revenueTrend}
          icon="revenue"
          color="success"
        />
      </Grid>
      
      <Grid item xs={12} sm={6} lg={3}>
        <KPICard
          title="Active Listings"
          value={metrics.activeListings}
          trend={metrics.listingsTrend}
          icon="listings"
          color="info"
        />
      </Grid>
      
      <Grid item xs={12} sm={6} lg={3}>
        <KPICard
          title="Pending Actions"
          value={metrics.pendingActions}
          trend={metrics.actionsTrend}
          icon="pending"
          color="warning"
          urgent={metrics.pendingActions > 10}
        />
      </Grid>
    </Grid>
  );
};
```

### KPI Card Component
```typescript
// src/components/dashboard/KPICard.tsx - Single Responsibility: Single metric display
import React from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  Avatar,
  Chip,
  IconButton
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  TrendingFlat,
  ShoppingCart,
  AttachMoney,
  List,
  Pending,
  MoreVert
} from '@mui/icons-material';

interface KPICardProps {
  title: string;
  value: string | number;
  trend?: {
    value: number;
    direction: 'up' | 'down' | 'flat';
    period: string;
  };
  icon: 'orders' | 'revenue' | 'listings' | 'pending';
  color: 'primary' | 'success' | 'info' | 'warning' | 'error';
  urgent?: boolean;
  onClick?: () => void;
}

const iconMap = {
  orders: ShoppingCart,
  revenue: AttachMoney,
  listings: List,
  pending: Pending
};

export const KPICard: React.FC<KPICardProps> = ({
  title,
  value,
  trend,
  icon,
  color,
  urgent,
  onClick
}) => {
  const IconComponent = iconMap[icon];

  const getTrendIcon = () => {
    if (!trend) return null;
    
    switch (trend.direction) {
      case 'up': return <TrendingUp sx={{ color: 'success.main' }} />;
      case 'down': return <TrendingDown sx={{ color: 'error.main' }} />;
      case 'flat': return <TrendingFlat sx={{ color: 'text.secondary' }} />;
    }
  };

  const getTrendColor = (): 'success' | 'error' | 'default' => {
    if (!trend) return 'default';
    
    switch (trend.direction) {
      case 'up': return 'success';
      case 'down': return 'error';
      case 'flat': return 'default';
    }
  };

  return (
    <Card 
      sx={{ 
        height: 120,
        cursor: onClick ? 'pointer' : 'default',
        border: urgent ? 2 : 0,
        borderColor: urgent ? 'warning.main' : 'transparent',
        '&:hover': onClick ? { elevation: 4 } : {}
      }}
      onClick={onClick}
    >
      <CardContent sx={{ p: 2, '&:last-child': { pb: 2 } }}>
        <Box sx={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
          <Box sx={{ flex: 1 }}>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              {title}
            </Typography>
            
            <Typography variant="h4" component="div" sx={{ mb: 1, fontWeight: 600 }}>
              {value}
            </Typography>
            
            {trend && (
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                {getTrendIcon()}
                <Chip
                  label={`${trend.value > 0 ? '+' : ''}${trend.value}% ${trend.period}`}
                  size="small"
                  color={getTrendColor()}
                  variant="outlined"
                />
              </Box>
            )}
          </Box>
          
          <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 1 }}>
            <Avatar sx={{ bgcolor: `${color}.main`, width: 40, height: 40 }}>
              <IconComponent />
            </Avatar>
            
            {urgent && (
              <Chip
                label="URGENT"
                size="small"
                color="warning"
                sx={{ fontSize: '0.7rem', height: 20 }}
              />
            )}
          </Box>
        </Box>
      </CardContent>
    </Card>
  );
};
```

### Performance Chart Component
```typescript
// src/components/dashboard/PerformanceChart.tsx - Single Responsibility: Chart visualization
import React, { useState } from 'react';
import {
  Card,
  CardContent,
  CardHeader,
  Box,
  ToggleButtonGroup,
  ToggleButton,
  Typography,
  useTheme
} from '@mui/material';
import {
  Line,
  LineChart,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend
} from 'recharts';

interface PerformanceData {
  date: string;
  revenue: number;
  orders: number;
  profit: number;
}

interface PerformanceChartProps {
  data?: PerformanceData[];
  loading?: boolean;
}

type ChartPeriod = '7d' | '30d' | '90d';
type ChartMetric = 'revenue' | 'orders' | 'profit' | 'all';

export const PerformanceChart: React.FC<PerformanceChartProps> = ({
  data = [],
  loading = false
}) => {
  const [period, setPeriod] = useState<ChartPeriod>('30d');
  const [metric, setMetric] = useState<ChartMetric>('all');
  const theme = useTheme();

  const handlePeriodChange = (_: React.MouseEvent<HTMLElement>, newPeriod: ChartPeriod | null) => {
    if (newPeriod) setPeriod(newPeriod);
  };

  const handleMetricChange = (_: React.MouseEvent<HTMLElement>, newMetric: ChartMetric | null) => {
    if (newMetric) setMetric(newMetric);
  };

  const getFilteredData = () => {
    const days = period === '7d' ? 7 : period === '30d' ? 30 : 90;
    return data.slice(-days);
  };

  const getMetricLines = () => {
    const lines = [];
    
    if (metric === 'revenue' || metric === 'all') {
      lines.push(
        <Line
          key="revenue"
          type="monotone"
          dataKey="revenue"
          stroke={theme.palette.success.main}
          strokeWidth={2}
          dot={{ fill: theme.palette.success.main, strokeWidth: 2, r: 4 }}
          name="Revenue ($)"
        />
      );
    }
    
    if (metric === 'orders' || metric === 'all') {
      lines.push(
        <Line
          key="orders"
          type="monotone"
          dataKey="orders"
          stroke={theme.palette.primary.main}
          strokeWidth={2}
          dot={{ fill: theme.palette.primary.main, strokeWidth: 2, r: 4 }}
          name="Orders"
        />
      );
    }
    
    if (metric === 'profit' || metric === 'all') {
      lines.push(
        <Line
          key="profit"
          type="monotone"
          dataKey="profit"
          stroke={theme.palette.info.main}
          strokeWidth={2}
          dot={{ fill: theme.palette.info.main, strokeWidth: 2, r: 4 }}
          name="Profit ($)"
        />
      );
    }
    
    return lines;
  };

  if (loading) {
    return (
      <Card sx={{ height: 400 }}>
        <CardHeader title="Performance Overview" />
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: 300 }}>
            <Typography variant="body2" color="text.secondary">
              Loading chart data...
            </Typography>
          </Box>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card sx={{ height: 400 }}>
      <CardHeader
        title="Performance Overview"
        action={
          <Box sx={{ display: 'flex', gap: 2 }}>
            <ToggleButtonGroup
              value={period}
              exclusive
              onChange={handlePeriodChange}
              size="small"
            >
              <ToggleButton value="7d">7 Days</ToggleButton>
              <ToggleButton value="30d">30 Days</ToggleButton>
              <ToggleButton value="90d">90 Days</ToggleButton>
            </ToggleButtonGroup>
            
            <ToggleButtonGroup
              value={metric}
              exclusive
              onChange={handleMetricChange}
              size="small"
            >
              <ToggleButton value="revenue">Revenue</ToggleButton>
              <ToggleButton value="orders">Orders</ToggleButton>
              <ToggleButton value="profit">Profit</ToggleButton>
              <ToggleButton value="all">All</ToggleButton>
            </ToggleButtonGroup>
          </Box>
        }
      />
      
      <CardContent sx={{ pt: 0 }}>
        <Box sx={{ height: 300, width: '100%' }}>
          <ResponsiveContainer>
            <LineChart data={getFilteredData()}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="date" 
                tick={{ fontSize: 12 }}
                axisLine={false}
              />
              <YAxis 
                tick={{ fontSize: 12 }}
                axisLine={false}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: theme.palette.background.paper,
                  border: `1px solid ${theme.palette.divider}`,
                  borderRadius: theme.shape.borderRadius
                }}
              />
              {metric === 'all' && <Legend />}
              {getMetricLines()}
            </LineChart>
          </ResponsiveContainer>
        </Box>
      </CardContent>
    </Card>
  );
};
```

### Quick Action Hub Component
```typescript
// src/components/dashboard/QuickActionHub.tsx - Single Responsibility: Action shortcuts
import React from 'react';
import {
  Card,
  CardHeader,
  CardContent,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Divider,
  Badge,
  Box
} from '@mui/material';
import {
  Upload,
  PriceChange,
  Assessment,
  Email,
  Inventory,
  Sync,
  Download,
  Settings
} from '@mui/icons-material';
import { useRouter } from 'next/router';

interface QuickAction {
  id: string;
  label: string;
  icon: React.ReactNode;
  path: string;
  badge?: number;
  color?: 'primary' | 'secondary' | 'error' | 'warning' | 'info' | 'success';
}

interface QuickActionHubProps {
  accountId: string;
}

export const QuickActionHub: React.FC<QuickActionHubProps> = ({ accountId }) => {
  const router = useRouter();

  const actions: QuickAction[] = [
    {
      id: 'import-csv',
      label: 'Import CSV Files',
      icon: <Upload />,
      path: `/accounts/${accountId}/import`,
      color: 'primary'
    },
    {
      id: 'bulk-pricing',
      label: 'Update Prices',
      icon: <PriceChange />,
      path: `/accounts/${accountId}/listings/bulk-edit`,
      color: 'info'
    },
    {
      id: 'reports',
      label: 'Generate Reports',
      icon: <Assessment />,
      path: `/accounts/${accountId}/reports`,
      color: 'success'
    },
    {
      id: 'messages',
      label: 'Messages',
      icon: <Email />,
      path: `/accounts/${accountId}/messages`,
      badge: 12,
      color: 'warning'
    },
    {
      id: 'inventory',
      label: 'Check Inventory',
      icon: <Inventory />,
      path: `/accounts/${accountId}/products`,
      badge: 5,
      color: 'error'
    },
    {
      id: 'sync',
      label: 'Sync Account',
      icon: <Sync />,
      path: `/accounts/${accountId}/sync`,
      color: 'secondary'
    },
    {
      id: 'export',
      label: 'Export Data',
      icon: <Download />,
      path: `/accounts/${accountId}/export`,
      color: 'primary'
    },
    {
      id: 'settings',
      label: 'Account Settings',
      icon: <Settings />,
      path: `/accounts/${accountId}/settings`,
      color: 'secondary'
    }
  ];

  const handleActionClick = (action: QuickAction) => {
    router.push(action.path);
  };

  return (
    <Card>
      <CardHeader 
        title="Quick Actions"
        titleTypographyProps={{ variant: 'h6' }}
      />
      <CardContent sx={{ pt: 0 }}>
        <List dense>
          {actions.map((action, index) => (
            <Box key={action.id}>
              <ListItem disablePadding>
                <ListItemButton
                  onClick={() => handleActionClick(action)}
                  sx={{
                    borderRadius: 1,
                    mb: 0.5,
                    '&:hover': {
                      backgroundColor: `${action.color}.50`
                    }
                  }}
                >
                  <ListItemIcon>
                    <Badge 
                      badgeContent={action.badge} 
                      color={action.color}
                      invisible={!action.badge}
                    >
                      {action.icon}
                    </Badge>
                  </ListItemIcon>
                  <ListItemText
                    primary={action.label}
                    primaryTypographyProps={{
                      variant: 'body2',
                      fontWeight: action.badge ? 600 : 400
                    }}
                  />
                </ListItemButton>
              </ListItem>
              {index < actions.length - 1 && index % 2 === 1 && <Divider sx={{ my: 1 }} />}
            </Box>
          ))}
        </List>
      </CardContent>
    </Card>
  );
};
```

## Implementation Tasks

### Task 1: Dashboard Layout & Structure
1. **Create Main Dashboard Component**
   - Implement responsive grid layout
   - Add loading states and error boundaries
   - Set up dashboard routing and navigation

2. **Implement Account Switching**
   - Create account dropdown with health indicators
   - Add account search and filtering
   - Implement account sync functionality

3. **Test Layout Components**
   - Responsive design testing on different screen sizes
   - Account switching functionality testing
   - Navigation integration testing

### Task 2: KPI Cards Implementation
1. **Create KPI Card Component**
   - Design metric display with trend indicators
   - Add click-through navigation to detailed views
   - Implement urgent/attention highlighting

2. **Build KPI Section**
   - Create responsive grid of KPI cards
   - Add loading skeletons and error states
   - Implement real-time data updates

3. **Test KPI Functionality**
   - Metric calculation accuracy testing
   - Trend visualization testing
   - Click-through navigation testing

### Task 3: Performance Chart Integration
1. **Implement Chart Component**
   - Set up Recharts with custom styling
   - Add multiple metrics and time periods
   - Create interactive chart controls

2. **Add Chart Data Management**
   - Implement data filtering and aggregation
   - Add chart type switching functionality
   - Create responsive chart sizing

3. **Test Chart Features**
   - Data visualization accuracy testing
   - Interactive controls testing
   - Responsive behavior testing

### Task 4: Quick Actions & Activity Feed
1. **Create Quick Action Hub**
   - Implement action shortcuts with badges
   - Add contextual actions based on account state
   - Create action routing and navigation

2. **Build Activity Feed**
   - Create real-time activity display
   - Add activity filtering and categorization
   - Implement activity click-through navigation

3. **Test Action Components**
   - Quick action functionality testing
   - Activity feed real-time updates testing
   - Navigation and routing testing

### Task 5: Real-Time Data Integration
1. **Implement Data Hooks**
   - Create dashboard data fetching hooks
   - Add real-time update mechanisms
   - Implement data caching and optimization

2. **Add WebSocket Integration**
   - Set up real-time data connections
   - Implement optimistic updates
   - Add connection status indicators

3. **Test Real-Time Features**
   - Data synchronization testing
   - WebSocket connection testing
   - Performance under load testing

## Quality Gates

### Performance Requirements
- [ ] Dashboard initial load: <2 seconds
- [ ] KPI updates: <500ms
- [ ] Chart rendering: <1 second
- [ ] Account switching: <300ms
- [ ] Memory usage: <50MB for dashboard

### Functionality Requirements
- [ ] All KPIs display accurate data
- [ ] Charts render correctly across all time periods
- [ ] Account switching preserves user context
- [ ] Quick actions navigate to correct destinations
- [ ] Real-time updates work without page refresh

### SOLID Compliance Checklist
- [ ] Each component has single, clear responsibility
- [ ] Chart components are interchangeable
- [ ] Dashboard widgets are extensible
- [ ] Data sources are abstracted and injected
- [ ] Interface segregation between read/write operations

---
**Next Phase**: Order Management Interface with CSV-driven workflow and smart grouping.