import { rest } from 'msw';
import { 
  createMockAccounts, 
  createMockUsers, 
  createMockPermissions, 
  createMockSettings, 
  createMockMetrics,
  createMockAccount,
  createMockUser,
  createMockPermission,
  createMockSetting,
  createMockApiError
} from '../utils/mockData';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

/**
 * MSW Handlers for Sprint 7 Account Management APIs
 * 
 * Following SOLID Principles:
 * - Single Responsibility: Each handler manages one endpoint
 * - Open/Closed: Easy to add new endpoints without modifying existing
 * - Interface Segregation: Focused request/response handling
 */

export const handlers = [
  // Authentication endpoints
  rest.post(`${API_BASE_URL}/api/v1/login`, (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        access_token: 'mock-jwt-token',
        token_type: 'bearer'
      })
    );
  }),

  rest.get(`${API_BASE_URL}/api/v1/me`, (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json(createMockUser())
    );
  }),

  // Users endpoints
  rest.get(`${API_BASE_URL}/api/v1/users`, (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json(createMockUsers())
    );
  }),

  rest.get(`${API_BASE_URL}/api/v1/users/:id`, (req, res, ctx) => {
    const { id } = req.params;
    return res(
      ctx.status(200),
      ctx.json(createMockUser({ id: parseInt(id as string) }))
    );
  }),

  // Accounts endpoints
  rest.get(`${API_BASE_URL}/api/v1/accounts`, (req, res, ctx) => {
    const accounts = createMockAccounts();
    return res(
      ctx.status(200),
      ctx.json(accounts)
    );
  }),

  rest.get(`${API_BASE_URL}/api/v1/accounts/:id/details`, (req, res, ctx) => {
    const { id } = req.params;
    const account = createMockAccount({ id: parseInt(id as string) });
    return res(
      ctx.status(200),
      ctx.json({
        ...account,
        settings: {},
        performance_metrics: {},
        user_permissions: createMockPermissions(parseInt(id as string)),
      })
    );
  }),

  rest.post(`${API_BASE_URL}/api/v1/accounts`, async (req, res, ctx) => {
    const body = await req.json();
    const newAccount = createMockAccount({
      id: Date.now(),
      name: body.name,
      platform_username: body.platform_username,
      user_id: body.user_id,
      is_active: body.is_active ?? true,
    });
    
    return res(
      ctx.status(201),
      ctx.json(newAccount)
    );
  }),

  rest.put(`${API_BASE_URL}/api/v1/accounts/:id`, async (req, res, ctx) => {
    const { id } = req.params;
    const updates = await req.json();
    const updatedAccount = createMockAccount({
      id: parseInt(id as string),
      ...updates,
      updated_at: new Date().toISOString(),
    });
    
    return res(
      ctx.status(200),
      ctx.json(updatedAccount)
    );
  }),

  rest.delete(`${API_BASE_URL}/api/v1/accounts/:id`, (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({ message: 'Account deactivated successfully' })
    );
  }),

  rest.post(`${API_BASE_URL}/api/v1/accounts/switch`, async (req, res, ctx) => {
    const { account_id } = await req.json();
    const account = createMockAccount({ id: account_id });
    
    return res(
      ctx.status(200),
      ctx.json({
        message: 'Account switched successfully',
        active_account: {
          id: account.id,
          name: account.name,
          platform_username: account.platform_username,
        },
      })
    );
  }),

  // Permissions endpoints
  rest.get(`${API_BASE_URL}/api/v1/accounts/:accountId/permissions`, (req, res, ctx) => {
    const { accountId } = req.params;
    const permissions = createMockPermissions(parseInt(accountId as string));
    
    return res(
      ctx.status(200),
      ctx.json(permissions)
    );
  }),

  rest.post(`${API_BASE_URL}/api/v1/accounts/:accountId/permissions`, async (req, res, ctx) => {
    const { accountId } = req.params;
    const body = await req.json();
    
    const newPermission = createMockPermission({
      id: Date.now(),
      account_id: parseInt(accountId as string),
      user_id: body.user_id,
      permission_level: body.permission_level,
      notes: body.notes,
      granted_at: new Date().toISOString(),
    });
    
    return res(
      ctx.status(201),
      ctx.json(newPermission)
    );
  }),

  rest.put(`${API_BASE_URL}/api/v1/accounts/:accountId/permissions/:permissionId`, async (req, res, ctx) => {
    const { accountId, permissionId } = req.params;
    const updates = await req.json();
    
    const updatedPermission = createMockPermission({
      id: parseInt(permissionId as string),
      account_id: parseInt(accountId as string),
      ...updates,
      granted_at: new Date().toISOString(),
    });
    
    return res(
      ctx.status(200),
      ctx.json(updatedPermission)
    );
  }),

  rest.delete(`${API_BASE_URL}/api/v1/accounts/:accountId/permissions/:permissionId`, (req, res, ctx) => {
    return res(ctx.status(204));
  }),

  rest.get(`${API_BASE_URL}/api/v1/users/:userId/permissions`, (req, res, ctx) => {
    const { userId } = req.params;
    const permissions = createMockPermissions(1, 2).map(p => ({
      ...p,
      user_id: parseInt(userId as string)
    }));
    
    return res(
      ctx.status(200),
      ctx.json(permissions)
    );
  }),

  // Settings endpoints
  rest.get(`${API_BASE_URL}/api/v1/accounts/:accountId/settings`, (req, res, ctx) => {
    const { accountId } = req.params;
    const settings = createMockSettings(parseInt(accountId as string));
    
    return res(
      ctx.status(200),
      ctx.json(settings)
    );
  }),

  rest.put(`${API_BASE_URL}/api/v1/accounts/:accountId/settings`, async (req, res, ctx) => {
    const { accountId } = req.params;
    const settingsUpdates = await req.json();
    
    return res(
      ctx.status(200),
      ctx.json({
        message: 'Settings updated successfully',
        updated_count: settingsUpdates.length,
      })
    );
  }),

  // Metrics endpoints
  rest.get(`${API_BASE_URL}/api/v1/accounts/:accountId/metrics`, (req, res, ctx) => {
    const { accountId } = req.params;
    const period = req.url.searchParams.get('period') || '30d';
    
    let days = 30;
    switch (period) {
      case '7d': days = 7; break;
      case '30d': days = 30; break;
      case '90d': days = 90; break;
      case '1y': days = 365; break;
    }
    
    const metrics = createMockMetrics(parseInt(accountId as string), days);
    
    return res(
      ctx.status(200),
      ctx.json(metrics)
    );
  }),

  rest.get(`${API_BASE_URL}/api/v1/accounts/:accountId/metrics/summary`, (req, res, ctx) => {
    const { accountId } = req.params;
    const latestMetrics = createMockMetrics(parseInt(accountId as string), 1)[0];
    
    return res(
      ctx.status(200),
      ctx.json({
        total_revenue: latestMetrics.total_revenue,
        total_orders: latestMetrics.total_orders,
        active_listings: latestMetrics.active_listings,
        conversion_rate: latestMetrics.conversion_rate,
      })
    );
  }),

  // Global search endpoint
  rest.get(`${API_BASE_URL}/api/v1/search`, (req, res, ctx) => {
    const query = req.url.searchParams.get('q');
    
    if (!query || query.length < 2) {
      return res(ctx.status(200), ctx.json([]));
    }

    // Mock search results
    const mockResults = [
      {
        type: 'account',
        id: '1',
        title: 'Primary Store',
        subtitle: 'primarystore@ebay.com',
        status: 'active',
      },
      {
        type: 'order',
        id: '12345',
        title: 'Order #12345',
        subtitle: 'iPhone 13 Pro Max',
        status: 'completed',
      },
      {
        type: 'listing',
        id: '67890',
        title: 'iPhone 13 Pro Max - 256GB',
        subtitle: 'Electronics > Phones',
        status: 'active',
      },
    ].filter(result => 
      result.title.toLowerCase().includes(query.toLowerCase()) ||
      result.subtitle.toLowerCase().includes(query.toLowerCase())
    );
    
    return res(
      ctx.status(200),
      ctx.json(mockResults)
    );
  }),

  // Error simulation handlers for testing
  rest.get(`${API_BASE_URL}/api/v1/accounts/error`, (req, res, ctx) => {
    return res(
      ctx.status(500),
      ctx.json({ message: 'Internal server error' })
    );
  }),

  rest.get(`${API_BASE_URL}/api/v1/accounts/unauthorized`, (req, res, ctx) => {
    return res(
      ctx.status(401),
      ctx.json({ message: 'Unauthorized access' })
    );
  }),

  rest.get(`${API_BASE_URL}/api/v1/accounts/not-found`, (req, res, ctx) => {
    return res(
      ctx.status(404),
      ctx.json({ message: 'Account not found' })
    );
  }),
];

export default handlers;