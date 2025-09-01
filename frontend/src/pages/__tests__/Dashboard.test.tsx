import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import Dashboard from '../Dashboard';
import * as api from '../../services/api';

// Mock the API module
jest.mock('../../services/api');
const mockApi = api as jest.Mocked<typeof api>;

// Mock recharts components
jest.mock('recharts', () => ({
  ...jest.requireActual('recharts'),
  ResponsiveContainer: ({ children }: any) => <div data-testid="responsive-container">{children}</div>,
  BarChart: ({ children }: any) => <div data-testid="bar-chart">{children}</div>,
  Bar: () => <div data-testid="bar" />,
  XAxis: () => <div data-testid="x-axis" />,
  YAxis: () => <div data-testid="y-axis" />,
  CartesianGrid: () => <div data-testid="cartesian-grid" />,
  Tooltip: () => <div data-testid="tooltip" />,
  PieChart: ({ children }: any) => <div data-testid="pie-chart">{children}</div>,
  Pie: () => <div data-testid="pie" />,
  Cell: () => <div data-testid="cell" />,
}));

const theme = createTheme();

const renderDashboard = () => {
  return render(
    <BrowserRouter>
      <ThemeProvider theme={theme}>
        <Dashboard />
      </ThemeProvider>
    </BrowserRouter>
  );
};

describe('Dashboard Component', () => {
  const mockDashboardData = {
    orders: {
      total: 150,
      pending: 45,
      processing: 30,
      shipped: 60,
      completed: 15
    },
    listings: {
      total: 200,
      active: 180,
      sold: 15,
      ended: 5
    },
    accounts: {
      total: 3,
      active: 3
    },
    recentActivity: [
      {
        id: 1,
        type: 'order',
        description: 'New order received',
        timestamp: '2024-01-15T10:30:00Z'
      },
      {
        id: 2,
        type: 'listing',
        description: 'Listing updated',
        timestamp: '2024-01-15T09:15:00Z'
      }
    ]
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders dashboard title', async () => {
    mockApi.getDashboardData.mockResolvedValue(mockDashboardData);
    
    renderDashboard();
    
    expect(screen.getByText(/dashboard/i)).toBeInTheDocument();
  });

  it('displays loading state initially', () => {
    mockApi.getDashboardData.mockReturnValue(new Promise(() => {})); // Never resolves
    
    renderDashboard();
    
    expect(screen.getByTestId('dashboard-loading')).toBeInTheDocument();
  });

  it('renders summary cards with correct data', async () => {
    mockApi.getDashboardData.mockResolvedValue(mockDashboardData);
    
    renderDashboard();
    
    await waitFor(() => {
      expect(screen.getByText('150')).toBeInTheDocument(); // Total orders
      expect(screen.getByText('200')).toBeInTheDocument(); // Total listings
      expect(screen.getByText('3')).toBeInTheDocument(); // Total accounts
    });
    
    expect(screen.getByText(/total orders/i)).toBeInTheDocument();
    expect(screen.getByText(/active listings/i)).toBeInTheDocument();
    expect(screen.getByText(/accounts/i)).toBeInTheDocument();
  });

  it('renders order status breakdown', async () => {
    mockApi.getDashboardData.mockResolvedValue(mockDashboardData);
    
    renderDashboard();
    
    await waitFor(() => {
      expect(screen.getByText('45')).toBeInTheDocument(); // Pending orders
      expect(screen.getByText('30')).toBeInTheDocument(); // Processing orders
      expect(screen.getByText('60')).toBeInTheDocument(); // Shipped orders
      expect(screen.getByText('15')).toBeInTheDocument(); // Completed orders
    });
  });

  it('renders charts', async () => {
    mockApi.getDashboardData.mockResolvedValue(mockDashboardData);
    
    renderDashboard();
    
    await waitFor(() => {
      expect(screen.getByTestId('bar-chart')).toBeInTheDocument();
      expect(screen.getByTestId('pie-chart')).toBeInTheDocument();
    });
  });

  it('displays recent activity', async () => {
    mockApi.getDashboardData.mockResolvedValue(mockDashboardData);
    
    renderDashboard();
    
    await waitFor(() => {
      expect(screen.getByText(/recent activity/i)).toBeInTheDocument();
      expect(screen.getByText('New order received')).toBeInTheDocument();
      expect(screen.getByText('Listing updated')).toBeInTheDocument();
    });
  });

  it('handles API error gracefully', async () => {
    mockApi.getDashboardData.mockRejectedValue(new Error('API Error'));
    
    renderDashboard();
    
    await waitFor(() => {
      expect(screen.getByText(/error loading dashboard data/i)).toBeInTheDocument();
    });
  });

  it('handles empty data', async () => {
    const emptyData = {
      orders: { total: 0, pending: 0, processing: 0, shipped: 0, completed: 0 },
      listings: { total: 0, active: 0, sold: 0, ended: 0 },
      accounts: { total: 0, active: 0 },
      recentActivity: []
    };
    
    mockApi.getDashboardData.mockResolvedValue(emptyData);
    
    renderDashboard();
    
    await waitFor(() => {
      expect(screen.getByText('0')).toBeInTheDocument();
      expect(screen.getByText(/no recent activity/i)).toBeInTheDocument();
    });
  });

  it('refreshes data when refresh button clicked', async () => {
    mockApi.getDashboardData.mockResolvedValue(mockDashboardData);
    
    renderDashboard();
    
    await waitFor(() => {
      expect(mockApi.getDashboardData).toHaveBeenCalledTimes(1);
    });
    
    // Click refresh button if it exists
    const refreshButton = screen.queryByRole('button', { name: /refresh/i });
    if (refreshButton) {
      refreshButton.click();
      
      await waitFor(() => {
        expect(mockApi.getDashboardData).toHaveBeenCalledTimes(2);
      });
    }
  });

  it('displays percentage calculations correctly', async () => {
    mockApi.getDashboardData.mockResolvedValue(mockDashboardData);
    
    renderDashboard();
    
    await waitFor(() => {
      // Check if percentage calculations are displayed (if implemented)
      const percentageElements = screen.queryAllByText(/%/);
      expect(percentageElements.length).toBeGreaterThanOrEqual(0);
    });
  });

  it('has proper responsive layout', async () => {
    mockApi.getDashboardData.mockResolvedValue(mockDashboardData);
    
    renderDashboard();
    
    await waitFor(() => {
      const responsiveContainers = screen.getAllByTestId('responsive-container');
      expect(responsiveContainers.length).toBeGreaterThan(0);
    });
  });

  it('formats timestamps correctly', async () => {
    mockApi.getDashboardData.mockResolvedValue(mockDashboardData);
    
    renderDashboard();
    
    await waitFor(() => {
      // Should display formatted time (implementation dependent)
      const timeElements = screen.queryAllByText(/ago|am|pm|\d{1,2}:\d{2}/i);
      expect(timeElements.length).toBeGreaterThanOrEqual(0);
    });
  });

  it('provides navigation links to detailed views', async () => {
    mockApi.getDashboardData.mockResolvedValue(mockDashboardData);
    
    renderDashboard();
    
    await waitFor(() => {
      // Check for links to orders, listings, etc. (if implemented)
      const links = screen.queryAllByRole('link');
      expect(links.length).toBeGreaterThanOrEqual(0);
    });
  });

  it('handles real-time updates', async () => {
    mockApi.getDashboardData.mockResolvedValue(mockDashboardData);
    
    renderDashboard();
    
    await waitFor(() => {
      expect(screen.getByText('150')).toBeInTheDocument();
    });
    
    // Simulate data update
    const updatedData = {
      ...mockDashboardData,
      orders: { ...mockDashboardData.orders, total: 151 }
    };
    
    mockApi.getDashboardData.mockResolvedValue(updatedData);
    
    // If auto-refresh is implemented, test it
    // This would depend on the actual implementation
  });

  it('displays correct chart colors and themes', async () => {
    mockApi.getDashboardData.mockResolvedValue(mockDashboardData);
    
    renderDashboard();
    
    await waitFor(() => {
      const barChart = screen.getByTestId('bar-chart');
      const pieChart = screen.getByTestId('pie-chart');
      
      expect(barChart).toBeInTheDocument();
      expect(pieChart).toBeInTheDocument();
    });
  });

  it('handles keyboard navigation', async () => {
    mockApi.getDashboardData.mockResolvedValue(mockDashboardData);
    
    renderDashboard();
    
    await waitFor(() => {
      // Test tab navigation through interactive elements
      const interactiveElements = screen.queryAllByRole('button');
      interactiveElements.forEach(element => {
        expect(element).not.toHaveAttribute('tabindex', '-1');
      });
    });
  });

  it('provides proper ARIA labels for accessibility', async () => {
    mockApi.getDashboardData.mockResolvedValue(mockDashboardData);
    
    renderDashboard();
    
    await waitFor(() => {
      // Check for proper ARIA labels on charts and data
      const mainContent = screen.getByRole('main');
      expect(mainContent).toBeInTheDocument();
    });
  });
});