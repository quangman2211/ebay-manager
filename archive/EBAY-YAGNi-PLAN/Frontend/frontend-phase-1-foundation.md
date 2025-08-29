# Frontend Phase 1: Foundation & Design System Implementation

## Overview
Establish foundational architecture and design system for eBay Management System frontend. Creates reusable component library, type system, and service architecture following SOLID principles.

## SOLID/YAGNI Compliance Strategy

### Single Responsibility Principle (SRP)
- **Design Tokens**: Only handle theme values and design constants
- **Base Components**: Each component handles one UI pattern only
- **API Services**: Each service manages one domain (orders, listings, etc.)
- **Type Definitions**: Each interface represents one data entity
- **Custom Hooks**: Each hook manages one specific state concern

### Open/Closed Principle (OCP)
- **Theme System**: Extensible color palette and typography without changing core
- **Component Library**: Add new variants without modifying existing components
- **Service Layer**: New API endpoints through configuration, not code changes
- **Icon System**: Pluggable icon sets through provider pattern

### Liskov Substitution Principle (LSP)
- **Component Interfaces**: All button variants interchangeable through same props
- **Service Implementations**: Mock services substitutable for real API services
- **Chart Components**: All chart types follow same data input interface

### Interface Segregation Principle (ISP)
- **Component Props**: Separate interfaces for different use cases (read-only vs editable)
- **Service Interfaces**: Segregated by operations (IReader, IWriter, IValidator)
- **Hook Interfaces**: Granular hooks instead of monolithic state management

### Dependency Inversion Principle (DIP)
- **Service Injection**: Components depend on service interfaces, not implementations
- **Configuration**: All settings injected via context providers
- **API Integration**: Abstract HTTP client, configurable endpoints

## Design System: "eBay Command Pro"

### Color Palette
```typescript
// src/styles/theme/colors.ts - Single Responsibility: Color definitions
export const colors = {
  primary: {
    50: '#E3F2FD',
    100: '#BBDEFB', 
    500: '#0064D2',  // eBay Blue
    600: '#0056B8',
    900: '#003C82'
  },
  success: {
    50: '#E8F5E8',
    500: '#00A650',  // eBay Green
    600: '#008A43'
  },
  warning: {
    50: '#FFF8E1',
    500: '#F5AF02',  // eBay Orange
    600: '#E09F00'
  },
  error: {
    50: '#FFEBEE',
    500: '#F44336',
    600: '#D32F2F'
  },
  gray: {
    50: '#F8F9FA',
    100: '#E9ECEF',
    200: '#DEE2E6',
    300: '#CED4DA',
    500: '#6C757D',
    700: '#495057',
    900: '#212529'
  },
  background: {
    default: '#FFFFFF',
    paper: '#F8F9FA',
    sidebar: '#FFFFFF'
  }
};
```

### Typography System
```typescript
// src/styles/theme/typography.ts - Single Responsibility: Typography definitions
export const typography = {
  fontFamily: {
    primary: 'Roboto, -apple-system, BlinkMacSystemFont, sans-serif',
    mono: 'JetBrains Mono, Consolas, Monaco, monospace'
  },
  fontSize: {
    xs: '0.75rem',    // 12px
    sm: '0.875rem',   // 14px  
    base: '1rem',     // 16px
    lg: '1.125rem',   // 18px
    xl: '1.25rem',    // 20px
    '2xl': '1.5rem',  // 24px
    '3xl': '1.875rem' // 30px
  },
  fontWeight: {
    normal: 400,
    medium: 500,
    semibold: 600,
    bold: 700
  },
  lineHeight: {
    tight: 1.25,
    base: 1.5,
    relaxed: 1.75
  }
};
```

### Component Spacing System
```typescript
// src/styles/theme/spacing.ts - Single Responsibility: Spacing definitions
export const spacing = {
  0: '0px',
  1: '0.25rem',  // 4px
  2: '0.5rem',   // 8px
  3: '0.75rem',  // 12px
  4: '1rem',     // 16px
  5: '1.25rem',  // 20px
  6: '1.5rem',   // 24px
  8: '2rem',     // 32px
  10: '2.5rem',  // 40px
  12: '3rem',    // 48px
  16: '4rem',    // 64px
  20: '5rem',    // 80px
  24: '6rem'     // 96px
};
```

## TypeScript Interface System

### Core Data Types
```typescript
// src/types/common.ts - Single Responsibility: Common type definitions
export type Status = 'active' | 'inactive' | 'pending' | 'completed' | 'cancelled';

export interface BaseEntity {
  id: string;
  createdAt: Date;
  updatedAt: Date;
}

export interface PaginationParams {
  page: number;
  limit: number;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
}

export interface ApiResponse<T> {
  data: T;
  message: string;
  success: boolean;
  pagination?: {
    page: number;
    limit: number;
    total: number;
    totalPages: number;
  };
}
```

### eBay-Specific Types
```typescript
// src/types/ebay.ts - Single Responsibility: eBay domain types
export interface EbayAccount extends BaseEntity {
  username: string;
  displayName: string;
  isActive: boolean;
  lastSyncAt?: Date;
  health: 'good' | 'warning' | 'critical';
  metrics: {
    totalOrders: number;
    totalRevenue: number;
    activeListings: number;
    pendingActions: number;
  };
}

export interface EbayOrder extends BaseEntity {
  ebayOrderId: string;
  accountId: string;
  buyerUsername: string;
  buyerName: string;
  buyerEmail?: string;
  shippingAddress: Address;
  items: OrderItem[];
  orderTotal: number;
  orderStatus: OrderStatus;
  paymentStatus: PaymentStatus;
  shippingStatus: ShippingStatus;
  orderDate: Date;
  paidDate?: Date;
  shippedDate?: Date;
  deliveredDate?: Date;
  trackingNumber?: string;
}

export interface EbayListing extends BaseEntity {
  ebayItemId: string;
  accountId: string;
  title: string;
  sku: string;
  category: string;
  condition: string;
  currentPrice: number;
  quantityAvailable: number;
  quantitySold: number;
  watchers: number;
  format: 'FIXED_PRICE' | 'AUCTION';
  status: ListingStatus;
  startDate: Date;
  endDate: Date;
  performance: {
    viewCount: number;
    watchCount: number;
    conversionRate: number;
  };
}

export interface DraftListing extends BaseEntity {
  title: string;
  sku: string;
  category: string;
  description: string;
  price: number;
  condition: string;
  imagesUploaded: number;
  listingStatus: DraftStatus;
  completionPercentage: number;
  notes?: string;
  productId?: string;
  estimatedProfit: number;
}

export type OrderStatus = 'pending' | 'confirmed' | 'processing' | 'shipped' | 'delivered' | 'cancelled';
export type PaymentStatus = 'pending' | 'paid' | 'failed' | 'refunded';
export type ShippingStatus = 'not_shipped' | 'processing' | 'shipped' | 'in_transit' | 'delivered';
export type ListingStatus = 'draft' | 'active' | 'inactive' | 'sold' | 'ended' | 'suspended';
export type DraftStatus = 'incomplete' | 'pending_review' | 'complete' | 'pricing_review';
```

## Base Component Library

### Button Component (SOLID-Compliant)
```typescript
// src/components/common/Button/Button.tsx
import React from 'react';
import { styled } from '@mui/material/styles';
import { Button as MuiButton, ButtonProps as MuiButtonProps } from '@mui/material';

// Interface Segregation: Separate concerns for different button uses
interface BaseButtonProps {
  children: React.ReactNode;
  disabled?: boolean;
  fullWidth?: boolean;
}

interface ActionButtonProps extends BaseButtonProps {
  variant: 'primary' | 'secondary' | 'danger';
  size: 'small' | 'medium' | 'large';
  onClick: () => void;
}

interface LoadingButtonProps extends ActionButtonProps {
  loading: boolean;
}

// Single Responsibility: Only handle button styling and behavior
const StyledButton = styled(MuiButton)<{variant: string}>(({ theme, variant }) => ({
  borderRadius: theme.spacing(1),
  textTransform: 'none',
  fontWeight: theme.typography.fontWeightMedium,
  
  // Open/Closed: Extend styles without modifying base
  ...(variant === 'primary' && {
    backgroundColor: theme.palette.primary.main,
    color: theme.palette.primary.contrastText,
    '&:hover': {
      backgroundColor: theme.palette.primary.dark,
    },
  }),
  
  ...(variant === 'secondary' && {
    backgroundColor: theme.palette.grey[100],
    color: theme.palette.text.primary,
    '&:hover': {
      backgroundColor: theme.palette.grey[200],
    },
  }),
  
  ...(variant === 'danger' && {
    backgroundColor: theme.palette.error.main,
    color: theme.palette.error.contrastText,
    '&:hover': {
      backgroundColor: theme.palette.error.dark,
    },
  }),
}));

export const Button: React.FC<ActionButtonProps> = ({
  children,
  variant,
  size,
  disabled,
  fullWidth,
  onClick,
  ...props
}) => {
  return (
    <StyledButton
      variant={variant}
      size={size}
      disabled={disabled}
      fullWidth={fullWidth}
      onClick={onClick}
      {...props}
    >
      {children}
    </StyledButton>
  );
};

export const LoadingButton: React.FC<LoadingButtonProps> = ({
  loading,
  children,
  disabled,
  ...props
}) => {
  return (
    <Button
      {...props}
      disabled={disabled || loading}
    >
      {loading ? 'Loading...' : children}
    </Button>
  );
};
```

### DataTable Component (SOLID-Compliant)
```typescript
// src/components/common/DataTable/DataTable.tsx
import React from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Checkbox,
  TablePagination,
} from '@mui/material';

// Interface Segregation: Separate interfaces for different table needs
interface BaseTableProps<T> {
  data: T[];
  columns: TableColumn<T>[];
  loading?: boolean;
  emptyMessage?: string;
}

interface SelectableTableProps<T> extends BaseTableProps<T> {
  selectable: true;
  selectedItems: string[];
  onSelectionChange: (selectedIds: string[]) => void;
}

interface PaginatedTableProps<T> extends BaseTableProps<T> {
  pagination: true;
  page: number;
  rowsPerPage: number;
  totalCount: number;
  onPageChange: (page: number) => void;
  onRowsPerPageChange: (rowsPerPage: number) => void;
}

interface TableColumn<T> {
  id: string;
  label: string;
  accessor: keyof T | ((item: T) => React.ReactNode);
  sortable?: boolean;
  width?: number;
  align?: 'left' | 'center' | 'right';
}

type DataTableProps<T> = BaseTableProps<T> | SelectableTableProps<T> | PaginatedTableProps<T>;

// Single Responsibility: Only handle data display in table format
export function DataTable<T extends { id: string }>({
  data,
  columns,
  loading = false,
  emptyMessage = 'No data available',
  ...props
}: DataTableProps<T>) {
  const isSelectable = 'selectable' in props;
  const isPaginated = 'pagination' in props;

  const handleSelectAll = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (isSelectable) {
      const newSelectedItems = event.target.checked ? data.map(item => item.id) : [];
      props.onSelectionChange(newSelectedItems);
    }
  };

  const handleSelectItem = (itemId: string) => {
    if (isSelectable) {
      const currentIndex = props.selectedItems.indexOf(itemId);
      const newSelected = [...props.selectedItems];

      if (currentIndex === -1) {
        newSelected.push(itemId);
      } else {
        newSelected.splice(currentIndex, 1);
      }

      props.onSelectionChange(newSelected);
    }
  };

  const renderCellContent = (item: T, column: TableColumn<T>) => {
    if (typeof column.accessor === 'function') {
      return column.accessor(item);
    }
    return item[column.accessor] as React.ReactNode;
  };

  return (
    <TableContainer component={Paper}>
      <Table>
        <TableHead>
          <TableRow>
            {isSelectable && (
              <TableCell padding="checkbox">
                <Checkbox
                  indeterminate={props.selectedItems.length > 0 && props.selectedItems.length < data.length}
                  checked={data.length > 0 && props.selectedItems.length === data.length}
                  onChange={handleSelectAll}
                />
              </TableCell>
            )}
            {columns.map(column => (
              <TableCell
                key={column.id}
                align={column.align || 'left'}
                style={{ width: column.width }}
              >
                {column.label}
              </TableCell>
            ))}
          </TableRow>
        </TableHead>
        <TableBody>
          {loading ? (
            <TableRow>
              <TableCell colSpan={columns.length + (isSelectable ? 1 : 0)} align="center">
                Loading...
              </TableCell>
            </TableRow>
          ) : data.length === 0 ? (
            <TableRow>
              <TableCell colSpan={columns.length + (isSelectable ? 1 : 0)} align="center">
                {emptyMessage}
              </TableCell>
            </TableRow>
          ) : (
            data.map(item => (
              <TableRow key={item.id} hover>
                {isSelectable && (
                  <TableCell padding="checkbox">
                    <Checkbox
                      checked={props.selectedItems.indexOf(item.id) !== -1}
                      onChange={() => handleSelectItem(item.id)}
                    />
                  </TableCell>
                )}
                {columns.map(column => (
                  <TableCell key={column.id} align={column.align || 'left'}>
                    {renderCellContent(item, column)}
                  </TableCell>
                ))}
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>
      
      {isPaginated && (
        <TablePagination
          rowsPerPageOptions={[10, 25, 50, 100]}
          component="div"
          count={props.totalCount}
          rowsPerPage={props.rowsPerPage}
          page={props.page}
          onPageChange={(_, newPage) => props.onPageChange(newPage)}
          onRowsPerPageChange={(event) => props.onRowsPerPageChange(parseInt(event.target.value, 10))}
        />
      )}
    </TableContainer>
  );
}
```

### Status Badge Component
```typescript
// src/components/common/StatusBadge/StatusBadge.tsx
import React from 'react';
import { Chip, ChipProps } from '@mui/material';
import { styled } from '@mui/material/styles';

interface StatusBadgeProps {
  status: string;
  variant?: 'default' | 'outlined';
  size?: 'small' | 'medium';
}

// Single Responsibility: Only handle status display
const StyledChip = styled(Chip)<{statusType: string}>(({ theme, statusType }) => ({
  fontWeight: theme.typography.fontWeightMedium,
  
  // Open/Closed: Add new status types without modifying existing ones
  ...(statusType === 'success' && {
    backgroundColor: theme.palette.success.light,
    color: theme.palette.success.dark,
  }),
  
  ...(statusType === 'warning' && {
    backgroundColor: theme.palette.warning.light,
    color: theme.palette.warning.dark,
  }),
  
  ...(statusType === 'error' && {
    backgroundColor: theme.palette.error.light,
    color: theme.palette.error.dark,
  }),
  
  ...(statusType === 'info' && {
    backgroundColor: theme.palette.info.light,
    color: theme.palette.info.dark,
  }),
}));

// Status type mapping - easily extensible
const statusTypeMap: Record<string, string> = {
  // Order statuses
  'completed': 'success',
  'delivered': 'success',
  'shipped': 'info',
  'processing': 'warning',
  'pending': 'warning',
  'cancelled': 'error',
  
  // Listing statuses
  'active': 'success',
  'inactive': 'error',
  'sold': 'success',
  'ended': 'error',
  
  // Draft statuses
  'complete': 'success',
  'incomplete': 'error',
  'pending_review': 'warning',
  'pricing_review': 'warning',
};

export const StatusBadge: React.FC<StatusBadgeProps> = ({
  status,
  variant = 'default',
  size = 'small'
}) => {
  const statusType = statusTypeMap[status.toLowerCase()] || 'info';
  
  return (
    <StyledChip
      label={status.replace('_', ' ').toUpperCase()}
      statusType={statusType}
      variant={variant}
      size={size}
    />
  );
};
```

## Service Layer Architecture

### Base API Service
```typescript
// src/services/base/ApiService.ts - Single Responsibility: HTTP operations
import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';

interface ApiConfig {
  baseURL: string;
  timeout: number;
  headers?: Record<string, string>;
}

// Dependency Inversion: Abstract HTTP operations
export interface IApiClient {
  get<T>(url: string, config?: AxiosRequestConfig): Promise<T>;
  post<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T>;
  put<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T>;
  delete<T>(url: string, config?: AxiosRequestConfig): Promise<T>;
}

export class ApiService implements IApiClient {
  private client: AxiosInstance;

  constructor(config: ApiConfig) {
    this.client = axios.create(config);
    this.setupInterceptors();
  }

  private setupInterceptors() {
    // Request interceptor for auth tokens
    this.client.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('authToken');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response: AxiosResponse) => response,
      (error) => {
        if (error.response?.status === 401) {
          // Handle token expiry
          localStorage.removeItem('authToken');
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }

  async get<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.get<T>(url, config);
    return response.data;
  }

  async post<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.post<T>(url, data, config);
    return response.data;
  }

  async put<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.put<T>(url, data, config);
    return response.data;
  }

  async delete<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.delete<T>(url, config);
    return response.data;
  }
}
```

### Account Service
```typescript
// src/services/AccountService.ts - Single Responsibility: Account operations
import { IApiClient } from './base/ApiService';
import { EbayAccount, ApiResponse } from '../types';

// Interface Segregation: Separate read/write operations
interface IAccountReader {
  getAccounts(): Promise<EbayAccount[]>;
  getAccount(id: string): Promise<EbayAccount>;
  getAccountMetrics(id: string): Promise<EbayAccount['metrics']>;
}

interface IAccountWriter {
  updateAccount(id: string, data: Partial<EbayAccount>): Promise<EbayAccount>;
  syncAccount(id: string): Promise<void>;
}

interface IAccountService extends IAccountReader, IAccountWriter {}

export class AccountService implements IAccountService {
  constructor(private apiClient: IApiClient) {}

  async getAccounts(): Promise<EbayAccount[]> {
    const response = await this.apiClient.get<ApiResponse<EbayAccount[]>>('/accounts');
    return response.data;
  }

  async getAccount(id: string): Promise<EbayAccount> {
    const response = await this.apiClient.get<ApiResponse<EbayAccount>>(`/accounts/${id}`);
    return response.data;
  }

  async getAccountMetrics(id: string): Promise<EbayAccount['metrics']> {
    const response = await this.apiClient.get<ApiResponse<EbayAccount['metrics']>>(`/accounts/${id}/metrics`);
    return response.data;
  }

  async updateAccount(id: string, data: Partial<EbayAccount>): Promise<EbayAccount> {
    const response = await this.apiClient.put<ApiResponse<EbayAccount>>(`/accounts/${id}`, data);
    return response.data;
  }

  async syncAccount(id: string): Promise<void> {
    await this.apiClient.post(`/accounts/${id}/sync`);
  }
}
```

## State Management with Zustand

### Account Store
```typescript
// src/store/accountStore.ts - Single Responsibility: Account state management
import { create } from 'zustand';
import { EbayAccount } from '../types';

interface AccountState {
  // State
  accounts: EbayAccount[];
  currentAccount: EbayAccount | null;
  loading: boolean;
  error: string | null;
  
  // Actions - Interface Segregation
  setAccounts: (accounts: EbayAccount[]) => void;
  setCurrentAccount: (account: EbayAccount | null) => void;
  updateAccount: (id: string, updates: Partial<EbayAccount>) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  
  // Computed values
  getCurrentAccountId: () => string | null;
  getAccountById: (id: string) => EbayAccount | undefined;
}

export const useAccountStore = create<AccountState>((set, get) => ({
  // Initial state
  accounts: [],
  currentAccount: null,
  loading: false,
  error: null,
  
  // Actions
  setAccounts: (accounts) => set({ accounts }),
  
  setCurrentAccount: (account) => set({ currentAccount: account }),
  
  updateAccount: (id, updates) => set((state) => ({
    accounts: state.accounts.map(account => 
      account.id === id ? { ...account, ...updates } : account
    ),
    currentAccount: state.currentAccount?.id === id 
      ? { ...state.currentAccount, ...updates } 
      : state.currentAccount
  })),
  
  setLoading: (loading) => set({ loading }),
  
  setError: (error) => set({ error }),
  
  // Computed values
  getCurrentAccountId: () => get().currentAccount?.id || null,
  
  getAccountById: (id) => get().accounts.find(account => account.id === id),
}));
```

## Implementation Tasks

### Task 1: Project Setup
1. **Initialize React Project**
   - Create Vite + React + TypeScript project
   - Configure ESLint, Prettier, and pre-commit hooks
   - Set up folder structure following SOLID principles

2. **Install Dependencies**
   - Material-UI v5 with custom theme
   - Zustand for state management
   - React Query for server state
   - Axios for HTTP client

3. **Configure Development Environment**
   - Set up dev server with hot reload
   - Configure path aliases for cleaner imports
   - Set up testing environment with Jest and React Testing Library

### Task 2: Design System Implementation
1. **Create Theme System**
   - Define color palette matching eBay brand
   - Set up typography and spacing scales
   - Create Material-UI theme configuration

2. **Build Base Components**
   - Button with variants and loading states
   - DataTable with selection and pagination
   - StatusBadge for order/listing status
   - Form components (Input, Select, Checkbox)

3. **Test Component Library**
   - Create Storybook for component documentation
   - Write unit tests for all base components
   - Test accessibility compliance

### Task 3: Service Architecture
1. **Create API Integration Layer**
   - Base API service with interceptors
   - Domain-specific services (Account, Order, Listing)
   - Error handling and retry mechanisms

2. **Implement State Management**
   - Zustand stores for each domain
   - React Query for server state caching
   - Local storage persistence for user preferences

3. **Test Service Integration**
   - Mock API responses for development
   - Integration tests with real API endpoints
   - Error scenario testing

### Task 4: Routing & Layout
1. **Setup React Router**
   - Define route structure for all modules
   - Implement route guards for authentication
   - Set up lazy loading for code splitting

2. **Create Layout Components**
   - Main application layout with sidebar
   - Header with account switcher
   - Responsive breakpoint handling

3. **Test Navigation**
   - End-to-end navigation testing
   - Route protection testing
   - Mobile responsive testing

## Quality Gates

### Component Standards
- [ ] All components follow single responsibility principle
- [ ] Props interfaces properly segregated by use case
- [ ] No business logic mixed with presentation
- [ ] Consistent naming conventions
- [ ] Full TypeScript coverage with strict mode

### Performance Standards
- [ ] Component rendering time <16ms
- [ ] Bundle size for base components <100KB
- [ ] Memory leaks prevented with proper cleanup
- [ ] Lazy loading implemented for non-critical components

### Testing Standards
- [ ] >90% unit test coverage for components
- [ ] Integration tests for all services
- [ ] Accessibility tests pass WCAG 2.1 AA
- [ ] Cross-browser compatibility verified

---
**Next Phase**: Multi-Account Dashboard implementation with KPI cards and real-time updates.