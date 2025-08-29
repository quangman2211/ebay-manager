# Plan 4: Order Management Module

## Objective
Build comprehensive order management system with status tracking, bulk operations, tracking number updates, and customer management integration.

## Dependencies
- Plan 1: Database Setup & Foundation completed
- Plan 2: Authentication & User Management APIs completed  
- Plan 3: CSV Processing Engine completed

## File Structure Updates
```
src/
├── services/
│   ├── order.service.ts
│   ├── order-status.service.ts
│   ├── tracking.service.ts
│   └── customer.service.ts
├── controllers/
│   ├── order.controller.ts
│   └── tracking.controller.ts
├── routes/
│   ├── order.routes.ts
│   └── tracking.routes.ts
├── schemas/
│   ├── order.schema.ts
│   └── tracking.schema.ts
├── types/
│   ├── order.types.ts
│   └── tracking.types.ts
├── utils/
│   ├── order-helpers.ts
│   └── shipping-providers.ts
└── jobs/
    ├── order-sync.job.ts
    └── tracking-update.job.ts
```

## Implementation Files

### 1. Order Type Definitions
```typescript
// src/types/order.types.ts

export interface OrderFilter {
  status?: OrderStatus[];
  paymentStatus?: PaymentStatus[];
  shippingStatus?: ShippingStatus[];
  dateRange?: {
    start: Date;
    end: Date;
  };
  buyerUsername?: string;
  itemNumber?: string;
  trackingNumber?: string;
  minAmount?: number;
  maxAmount?: number;
}

export type OrderStatus = 'pending' | 'paid' | 'shipped' | 'delivered' | 'completed' | 'cancelled' | 'returned' | 'disputed';
export type PaymentStatus = 'unpaid' | 'pending' | 'paid' | 'refunded' | 'disputed';
export type ShippingStatus = 'unshipped' | 'processing' | 'shipped' | 'in_transit' | 'delivered' | 'returned';

export interface OrderStatusUpdate {
  orderId: number;
  newStatus: OrderStatus;
  trackingNumber?: string;
  shippingCarrier?: string;
  notes?: string;
  updatedBy: number;
}

export interface BulkOrderUpdate {
  orderIds: number[];
  updates: {
    status?: OrderStatus;
    shippingStatus?: ShippingStatus;
    trackingNumbers?: { [orderId: number]: string };
    shippingCarrier?: string;
    notes?: string;
  };
}

export interface TrackingInfo {
  trackingNumber: string;
  carrier: string;
  status: string;
  estimatedDelivery?: Date;
  currentLocation?: string;
  trackingEvents: TrackingEvent[];
  lastUpdated: Date;
}

export interface TrackingEvent {
  date: Date;
  status: string;
  location: string;
  description: string;
}

export interface OrderSummary {
  totalOrders: number;
  totalRevenue: number;
  averageOrderValue: number;
  statusBreakdown: { [key in OrderStatus]: number };
  paymentStatusBreakdown: { [key in PaymentStatus]: number };
  shippingStatusBreakdown: { [key in ShippingStatus]: number };
}

export interface ShippingProvider {
  name: string;
  trackingUrlPattern: string;
  apiEndpoint?: string;
  apiKey?: string;
  supportedServices: string[];
}
```

### 2. Order Schemas
```typescript
// src/schemas/order.schema.ts
import { z } from 'zod';

export const orderFilterSchema = z.object({
  status: z.array(z.enum(['pending', 'paid', 'shipped', 'delivered', 'completed', 'cancelled', 'returned', 'disputed'])).optional(),
  paymentStatus: z.array(z.enum(['unpaid', 'pending', 'paid', 'refunded', 'disputed'])).optional(),
  shippingStatus: z.array(z.enum(['unshipped', 'processing', 'shipped', 'in_transit', 'delivered', 'returned'])).optional(),
  dateRange: z.object({
    start: z.string().datetime(),
    end: z.string().datetime(),
  }).optional(),
  buyerUsername: z.string().max(100).optional(),
  itemNumber: z.string().max(50).optional(),
  trackingNumber: z.string().max(100).optional(),
  minAmount: z.number().min(0).optional(),
  maxAmount: z.number().min(0).optional(),
});

export const updateOrderStatusSchema = z.object({
  status: z.enum(['pending', 'paid', 'shipped', 'delivered', 'completed', 'cancelled', 'returned', 'disputed']).optional(),
  paymentStatus: z.enum(['unpaid', 'pending', 'paid', 'refunded', 'disputed']).optional(),
  shippingStatus: z.enum(['unshipped', 'processing', 'shipped', 'in_transit', 'delivered', 'returned']).optional(),
  trackingNumber: z.string().max(100).optional(),
  shippingCarrier: z.string().max(50).optional(),
  notes: z.string().max(1000).optional(),
});

export const bulkUpdateOrdersSchema = z.object({
  orderIds: z.array(z.number().positive()).min(1).max(100),
  updates: z.object({
    status: z.enum(['pending', 'paid', 'shipped', 'delivered', 'completed', 'cancelled', 'returned', 'disputed']).optional(),
    shippingStatus: z.enum(['unshipped', 'processing', 'shipped', 'in_transit', 'delivered', 'returned']).optional(),
    trackingNumbers: z.record(z.string(), z.string().max(100)).optional(),
    shippingCarrier: z.string().max(50).optional(),
    notes: z.string().max(1000).optional(),
  }),
});

export const trackingUpdateSchema = z.object({
  trackingNumber: z.string().min(1).max(100),
  carrier: z.string().min(1).max(50),
  status: z.string().max(100).optional(),
  estimatedDelivery: z.string().datetime().optional(),
  currentLocation: z.string().max(200).optional(),
});

export const bulkTrackingUploadSchema = z.object({
  orders: z.array(z.object({
    orderId: z.number().positive().optional(),
    ebayOrderId: z.string().optional(),
    trackingNumber: z.string().min(1).max(100),
    carrier: z.string().min(1).max(50),
  })).min(1).max(500),
});

export type OrderFilterInput = z.infer<typeof orderFilterSchema>;
export type UpdateOrderStatusInput = z.infer<typeof updateOrderStatusSchema>;
export type BulkUpdateOrdersInput = z.infer<typeof bulkUpdateOrdersSchema>;
export type TrackingUpdateInput = z.infer<typeof trackingUpdateSchema>;
export type BulkTrackingUploadInput = z.infer<typeof bulkTrackingUploadSchema>;
```

### 3. Customer Service
```typescript
// src/services/customer.service.ts
import { prisma } from '../config/database';
import { PaginationParams, FilterParams } from '../types/common.types';

export class CustomerService {
  async createOrUpdateCustomer(buyerData: {
    ebayUsername: string;
    email: string;
    fullName: string;
    address?: any;
    orderData: {
      totalAmount: number;
      orderDate: Date;
      accountId: number;
    };
  }) {
    // Check if customer exists
    let customer = await prisma.customer.findFirst({
      where: {
        OR: [
          { ebayUsername: buyerData.ebayUsername },
          { email: buyerData.email },
        ],
      },
    });

    const orderData = buyerData.orderData;
    
    if (customer) {
      // Update existing customer
      const totalOrders = await prisma.order.count({
        where: { 
          buyerUsername: buyerData.ebayUsername,
          ebayAccountId: orderData.accountId,
        },
      });
      
      const totalSpent = await prisma.order.aggregate({
        where: { 
          buyerUsername: buyerData.ebayUsername,
          ebayAccountId: orderData.accountId,
          paymentStatus: 'paid',
        },
        _sum: { totalAmount: true },
      });

      customer = await prisma.customer.update({
        where: { id: customer.id },
        data: {
          email: buyerData.email,
          fullName: buyerData.fullName,
          address: buyerData.address ? JSON.stringify(buyerData.address) : undefined,
          lastOrderDate: orderData.orderDate,
          totalOrders,
          totalSpent: totalSpent._sum.totalAmount || 0,
        },
      });
    } else {
      // Create new customer
      customer = await prisma.customer.create({
        data: {
          ebayUsername: buyerData.ebayUsername,
          email: buyerData.email,
          fullName: buyerData.fullName,
          address: buyerData.address ? JSON.stringify(buyerData.address) : null,
          customerType: 'new',
          firstOrderDate: orderData.orderDate,
          lastOrderDate: orderData.orderDate,
          totalOrders: 1,
          totalSpent: orderData.totalAmount,
        },
      });
    }

    // Update customer type based on order history
    await this.updateCustomerSegment(customer.id);
    
    return customer;
  }

  async updateCustomerSegment(customerId: number) {
    const customer = await prisma.customer.findUnique({
      where: { id: customerId },
    });

    if (!customer) return;

    let newCustomerType = 'new';
    let segmentValue = '';

    // Determine customer segment
    if (customer.totalOrders === 1) {
      newCustomerType = 'new';
    } else if (customer.totalOrders >= 2 && customer.totalOrders <= 5) {
      newCustomerType = 'returning';
    } else if (customer.totalOrders > 5 || customer.totalSpent > 1000) {
      newCustomerType = 'vip';
      segmentValue = customer.totalSpent > 5000 ? 'high_value' : 'frequent_buyer';
    }

    // Check if customer is at risk (no orders in 90 days)
    const daysSinceLastOrder = Math.floor(
      (new Date().getTime() - customer.lastOrderDate.getTime()) / (1000 * 60 * 60 * 24)
    );
    
    if (daysSinceLastOrder > 90 && customer.totalOrders > 1) {
      newCustomerType = 'at_risk';
      segmentValue = `${daysSinceLastOrder}_days_inactive`;
    }

    // Update customer type if changed
    if (customer.customerType !== newCustomerType) {
      await prisma.customer.update({
        where: { id: customerId },
        data: { customerType: newCustomerType },
      });

      // Create or update segment record
      await prisma.customerSegment.upsert({
        where: { customerId },
        update: {
          segmentType: newCustomerType,
          segmentValue,
          assignedAt: new Date(),
        },
        create: {
          customerId,
          segmentType: newCustomerType,
          segmentValue,
        },
      });
    }
  }

  async getCustomers(
    pagination: PaginationParams,
    filters: FilterParams & { customerType?: string; minSpent?: number; maxSpent?: number }
  ) {
    const { page = 1, limit = 20, sortBy = 'lastOrderDate', sortOrder = 'desc' } = pagination;
    const { search, customerType, minSpent, maxSpent } = filters;
    
    const skip = (page - 1) * limit;
    const where: any = {};

    if (search) {
      where.OR = [
        { ebayUsername: { contains: search, mode: 'insensitive' } },
        { email: { contains: search, mode: 'insensitive' } },
        { fullName: { contains: search, mode: 'insensitive' } },
      ];
    }

    if (customerType) {
      where.customerType = customerType;
    }

    if (minSpent !== undefined || maxSpent !== undefined) {
      where.totalSpent = {};
      if (minSpent !== undefined) where.totalSpent.gte = minSpent;
      if (maxSpent !== undefined) where.totalSpent.lte = maxSpent;
    }

    const [customers, total] = await Promise.all([
      prisma.customer.findMany({
        where,
        skip,
        take: limit,
        orderBy: { [sortBy]: sortOrder },
        include: {
          _count: {
            select: { segments: true },
          },
        },
      }),
      prisma.customer.count({ where }),
    ]);

    return {
      customers,
      pagination: {
        page,
        limit,
        total,
        totalPages: Math.ceil(total / limit),
      },
    };
  }

  async getCustomerById(customerId: number) {
    const customer = await prisma.customer.findUnique({
      where: { id: customerId },
      include: {
        segments: {
          orderBy: { assignedAt: 'desc' },
          take: 5,
        },
      },
    });

    if (!customer) {
      throw new Error('Customer not found');
    }

    // Get recent orders
    const recentOrders = await prisma.order.findMany({
      where: { buyerUsername: customer.ebayUsername },
      orderBy: { orderDate: 'desc' },
      take: 10,
      select: {
        id: true,
        ebayOrderId: true,
        totalAmount: true,
        orderDate: true,
        paymentStatus: true,
        shippingStatus: true,
        account: {
          select: { accountName: true },
        },
        orderItems: {
          select: {
            title: true,
            quantity: true,
            unitPrice: true,
          },
        },
      },
    });

    return {
      ...customer,
      recentOrders,
    };
  }
}
```

### 4. Order Status Service
```typescript
// src/services/order-status.service.ts
import { prisma } from '../config/database';
import { OrderStatus, PaymentStatus, ShippingStatus } from '../types/order.types';

export class OrderStatusService {
  
  async updateOrderStatus(
    orderId: number,
    updates: {
      status?: OrderStatus;
      paymentStatus?: PaymentStatus;
      shippingStatus?: ShippingStatus;
      trackingNumber?: string;
      shippingCarrier?: string;
      notes?: string;
    },
    updatedBy: number
  ) {
    const order = await prisma.order.findUnique({
      where: { id: orderId },
    });

    if (!order) {
      throw new Error('Order not found');
    }

    // Record status changes in history
    const statusHistory = [];
    
    if (updates.status && updates.status !== order.paymentStatus) {
      statusHistory.push({
        orderId,
        statusFrom: order.paymentStatus || 'unknown',
        statusTo: updates.status,
        updatedBy,
        notes: updates.notes,
      });
    }

    if (updates.shippingStatus && updates.shippingStatus !== order.shippingStatus) {
      statusHistory.push({
        orderId,
        statusFrom: order.shippingStatus || 'unshipped',
        statusTo: updates.shippingStatus,
        trackingNumber: updates.trackingNumber,
        updatedBy,
        notes: updates.notes,
      });
    }

    // Update order
    const updatedOrder = await prisma.$transaction(async (tx) => {
      // Update main order record
      const updated = await tx.order.update({
        where: { id: orderId },
        data: {
          paymentStatus: updates.status || order.paymentStatus,
          shippingStatus: updates.shippingStatus || order.shippingStatus,
          trackingNumber: updates.trackingNumber || order.trackingNumber,
        },
      });

      // Create status history records
      if (statusHistory.length > 0) {
        await tx.orderStatusHistory.createMany({
          data: statusHistory,
        });
      }

      return updated;
    });

    // Update customer data
    if (updates.status === 'paid' || updates.shippingStatus === 'delivered') {
      await this.updateCustomerFromOrder(orderId);
    }

    return updatedOrder;
  }

  async bulkUpdateOrders(
    orderIds: number[],
    updates: {
      status?: OrderStatus;
      shippingStatus?: ShippingStatus;
      trackingNumbers?: { [orderId: number]: string };
      shippingCarrier?: string;
      notes?: string;
    },
    updatedBy: number
  ) {
    const results = {
      updated: 0,
      failed: 0,
      errors: [] as string[],
    };

    // Process in batches to avoid overwhelming the database
    const batchSize = 10;
    for (let i = 0; i < orderIds.length; i += batchSize) {
      const batch = orderIds.slice(i, i + batchSize);
      
      const promises = batch.map(async (orderId) => {
        try {
          const orderUpdates = {
            status: updates.status,
            shippingStatus: updates.shippingStatus,
            trackingNumber: updates.trackingNumbers?.[orderId],
            shippingCarrier: updates.shippingCarrier,
            notes: updates.notes,
          };

          await this.updateOrderStatus(orderId, orderUpdates, updatedBy);
          results.updated++;
        } catch (error) {
          results.failed++;
          results.errors.push(`Order ${orderId}: ${error instanceof Error ? error.message : 'Unknown error'}`);
        }
      });

      await Promise.all(promises);
    }

    return results;
  }

  async getOrderStatusHistory(orderId: number) {
    const history = await prisma.orderStatusHistory.findMany({
      where: { orderId },
      orderBy: { updatedAt: 'desc' },
      include: {
        updatedByUser: {
          select: {
            username: true,
            fullName: true,
          },
        },
      },
    });

    return history;
  }

  async getOrderStatusSummary(accountId?: number, dateRange?: { start: Date; end: Date }) {
    const where: any = {};
    
    if (accountId) {
      where.ebayAccountId = accountId;
    }
    
    if (dateRange) {
      where.orderDate = {
        gte: dateRange.start,
        lte: dateRange.end,
      };
    }

    const [
      totalOrders,
      totalRevenue,
      statusBreakdown,
      paymentStatusBreakdown,
      shippingStatusBreakdown,
    ] = await Promise.all([
      prisma.order.count({ where }),
      prisma.order.aggregate({
        where: { ...where, paymentStatus: 'paid' },
        _sum: { totalAmount: true },
      }),
      prisma.order.groupBy({
        by: ['paymentStatus'],
        where,
        _count: { id: true },
      }),
      prisma.order.groupBy({
        by: ['paymentStatus'],
        where,
        _count: { id: true },
      }),
      prisma.order.groupBy({
        by: ['shippingStatus'],
        where,
        _count: { id: true },
      }),
    ]);

    const averageOrderValue = totalOrders > 0 ? (totalRevenue._sum.totalAmount || 0) / totalOrders : 0;

    return {
      totalOrders,
      totalRevenue: totalRevenue._sum.totalAmount || 0,
      averageOrderValue,
      statusBreakdown: this.formatBreakdown(statusBreakdown),
      paymentStatusBreakdown: this.formatBreakdown(paymentStatusBreakdown),
      shippingStatusBreakdown: this.formatBreakdown(shippingStatusBreakdown),
    };
  }

  private formatBreakdown(data: any[]) {
    const result: any = {};
    data.forEach(item => {
      result[item.paymentStatus || item.shippingStatus] = item._count.id;
    });
    return result;
  }

  private async updateCustomerFromOrder(orderId: number) {
    const order = await prisma.order.findUnique({
      where: { id: orderId },
      include: { account: true },
    });

    if (!order) return;

    const customerService = new (await import('./customer.service')).CustomerService();
    await customerService.createOrUpdateCustomer({
      ebayUsername: order.buyerUsername,
      email: order.buyerEmail,
      fullName: order.buyerUsername, // Fallback if full name not available
      orderData: {
        totalAmount: Number(order.totalAmount),
        orderDate: order.orderDate,
        accountId: order.ebayAccountId,
      },
    });
  }
}
```

### 5. Tracking Service
```typescript
// src/services/tracking.service.ts
import { prisma } from '../config/database';
import { TrackingInfo, ShippingProvider } from '../types/order.types';

export class TrackingService {
  private shippingProviders: ShippingProvider[] = [
    {
      name: 'USPS',
      trackingUrlPattern: 'https://tools.usps.com/go/TrackConfirmAction?tLabels={trackingNumber}',
      supportedServices: ['Priority Mail', 'First-Class Mail', 'Ground Advantage'],
    },
    {
      name: 'UPS',
      trackingUrlPattern: 'https://www.ups.com/track?tracknum={trackingNumber}',
      supportedServices: ['Ground', 'Next Day Air', '2nd Day Air'],
    },
    {
      name: 'FedEx',
      trackingUrlPattern: 'https://www.fedex.com/fedextrack/?trknbr={trackingNumber}',
      supportedServices: ['Ground', 'Express', 'Priority Overnight'],
    },
    {
      name: 'DHL',
      trackingUrlPattern: 'https://www.dhl.com/en/express/tracking.html?AWB={trackingNumber}',
      supportedServices: ['Express', 'Ground'],
    },
  ];

  async updateOrderTracking(
    orderId: number,
    trackingNumber: string,
    carrier: string,
    updatedBy: number
  ) {
    const order = await prisma.order.findUnique({
      where: { id: orderId },
    });

    if (!order) {
      throw new Error('Order not found');
    }

    // Update order with tracking info
    const updatedOrder = await prisma.order.update({
      where: { id: orderId },
      data: {
        trackingNumber,
        shippingStatus: 'shipped',
      },
    });

    // Create status history entry
    await prisma.orderStatusHistory.create({
      data: {
        orderId,
        statusFrom: order.shippingStatus || 'processing',
        statusTo: 'shipped',
        trackingNumber,
        updatedBy,
        notes: `Tracking number added: ${trackingNumber} (${carrier})`,
      },
    });

    return updatedOrder;
  }

  async bulkUpdateTracking(
    orders: Array<{
      orderId?: number;
      ebayOrderId?: string;
      trackingNumber: string;
      carrier: string;
    }>,
    accountId: number,
    updatedBy: number
  ) {
    const results = {
      updated: 0,
      failed: 0,
      notFound: 0,
      errors: [] as string[],
    };

    for (const orderUpdate of orders) {
      try {
        let order;
        
        if (orderUpdate.orderId) {
          order = await prisma.order.findFirst({
            where: {
              id: orderUpdate.orderId,
              ebayAccountId: accountId,
            },
          });
        } else if (orderUpdate.ebayOrderId) {
          order = await prisma.order.findFirst({
            where: {
              ebayOrderId: orderUpdate.ebayOrderId,
              ebayAccountId: accountId,
            },
          });
        }

        if (!order) {
          results.notFound++;
          results.errors.push(`Order not found: ${orderUpdate.orderId || orderUpdate.ebayOrderId}`);
          continue;
        }

        await this.updateOrderTracking(
          order.id,
          orderUpdate.trackingNumber,
          orderUpdate.carrier,
          updatedBy
        );
        
        results.updated++;
      } catch (error) {
        results.failed++;
        results.errors.push(
          `Order ${orderUpdate.orderId || orderUpdate.ebayOrderId}: ${
            error instanceof Error ? error.message : 'Unknown error'
          }`
        );
      }
    }

    return results;
  }

  getTrackingUrl(trackingNumber: string, carrier: string): string | null {
    const provider = this.shippingProviders.find(
      p => p.name.toLowerCase() === carrier.toLowerCase()
    );
    
    if (!provider) {
      return null;
    }
    
    return provider.trackingUrlPattern.replace('{trackingNumber}', trackingNumber);
  }

  async getOrdersWithoutTracking(accountId: number, limit: number = 50) {
    const orders = await prisma.order.findMany({
      where: {
        ebayAccountId: accountId,
        shippingStatus: { in: ['processing', 'shipped'] },
        OR: [
          { trackingNumber: null },
          { trackingNumber: '' },
        ],
      },
      select: {
        id: true,
        ebayOrderId: true,
        buyerUsername: true,
        totalAmount: true,
        orderDate: true,
        shippingStatus: true,
        orderItems: {
          select: {
            title: true,
            quantity: true,
          },
        },
      },
      orderBy: { orderDate: 'desc' },
      take: limit,
    });

    return orders;
  }

  async getOrdersNeedingShipment(accountId: number, limit: number = 50) {
    const orders = await prisma.order.findMany({
      where: {
        ebayAccountId: accountId,
        paymentStatus: 'paid',
        shippingStatus: { in: ['unshipped', 'processing'] },
      },
      select: {
        id: true,
        ebayOrderId: true,
        buyerUsername: true,
        buyerEmail: true,
        totalAmount: true,
        orderDate: true,
        shippingAddress: true,
        orderItems: {
          select: {
            title: true,
            quantity: true,
            sku: true,
          },
        },
      },
      orderBy: { orderDate: 'asc' },
      take: limit,
    });

    return orders;
  }

  getSupportedCarriers() {
    return this.shippingProviders.map(provider => ({
      name: provider.name,
      services: provider.supportedServices,
    }));
  }
}
```

### 6. Order Service
```typescript
// src/services/order.service.ts
import { prisma } from '../config/database';
import { OrderFilter } from '../types/order.types';
import { PaginationParams } from '../types/common.types';

export class OrderService {
  async getOrders(
    pagination: PaginationParams,
    filters: OrderFilter,
    accountIds?: number[]
  ) {
    const { page = 1, limit = 20, sortBy = 'orderDate', sortOrder = 'desc' } = pagination;
    const skip = (page - 1) * limit;
    
    const where: any = {};
    
    if (accountIds && accountIds.length > 0) {
      where.ebayAccountId = { in: accountIds };
    }
    
    if (filters.status && filters.status.length > 0) {
      where.paymentStatus = { in: filters.status };
    }
    
    if (filters.paymentStatus && filters.paymentStatus.length > 0) {
      where.paymentStatus = { in: filters.paymentStatus };
    }
    
    if (filters.shippingStatus && filters.shippingStatus.length > 0) {
      where.shippingStatus = { in: filters.shippingStatus };
    }
    
    if (filters.dateRange) {
      where.orderDate = {
        gte: filters.dateRange.start,
        lte: filters.dateRange.end,
      };
    }
    
    if (filters.buyerUsername) {
      where.buyerUsername = {
        contains: filters.buyerUsername,
        mode: 'insensitive',
      };
    }
    
    if (filters.trackingNumber) {
      where.trackingNumber = {
        contains: filters.trackingNumber,
        mode: 'insensitive',
      };
    }
    
    if (filters.itemNumber) {
      where.orderItems = {
        some: {
          itemNumber: parseInt(filters.itemNumber),
        },
      };
    }
    
    if (filters.minAmount !== undefined || filters.maxAmount !== undefined) {
      where.totalAmount = {};
      if (filters.minAmount !== undefined) where.totalAmount.gte = filters.minAmount;
      if (filters.maxAmount !== undefined) where.totalAmount.lte = filters.maxAmount;
    }

    const [orders, total] = await Promise.all([
      prisma.order.findMany({
        where,
        skip,
        take: limit,
        orderBy: { [sortBy]: sortOrder },
        include: {
          account: {
            select: {
              id: true,
              accountName: true,
            },
          },
          orderItems: {
            select: {
              title: true,
              quantity: true,
              unitPrice: true,
              sku: true,
            },
          },
          _count: {
            select: {
              statusHistory: true,
            },
          },
        },
      }),
      prisma.order.count({ where }),
    ]);

    return {
      orders: orders.map(order => ({
        ...order,
        shippingAddress: JSON.parse(order.shippingAddress as string),
        statusHistoryCount: order._count.statusHistory,
        _count: undefined,
      })),
      pagination: {
        page,
        limit,
        total,
        totalPages: Math.ceil(total / limit),
      },
    };
  }

  async getOrderById(orderId: number) {
    const order = await prisma.order.findUnique({
      where: { id: orderId },
      include: {
        account: {
          select: {
            id: true,
            accountName: true,
            accountEmail: true,
          },
        },
        orderItems: true,
        statusHistory: {
          orderBy: { updatedAt: 'desc' },
          include: {
            updatedByUser: {
              select: {
                username: true,
                fullName: true,
              },
            },
          },
        },
      },
    });

    if (!order) {
      throw new Error('Order not found');
    }

    return {
      ...order,
      shippingAddress: JSON.parse(order.shippingAddress as string),
    };
  }

  async exportOrders(filters: OrderFilter, accountIds?: number[], format: 'csv' | 'excel' = 'csv') {
    const where: any = {};
    
    if (accountIds && accountIds.length > 0) {
      where.ebayAccountId = { in: accountIds };
    }
    
    // Apply same filters as getOrders
    if (filters.status && filters.status.length > 0) {
      where.paymentStatus = { in: filters.status };
    }
    // ... (other filters)

    const orders = await prisma.order.findMany({
      where,
      include: {
        account: { select: { accountName: true } },
        orderItems: true,
      },
      orderBy: { orderDate: 'desc' },
    });

    // Transform data for export
    const exportData = orders.map(order => ({
      'Order ID': order.ebayOrderId,
      'Account': order.account.accountName,
      'Buyer Username': order.buyerUsername,
      'Buyer Email': order.buyerEmail,
      'Total Amount': order.totalAmount,
      'Currency': order.currency,
      'Order Date': order.orderDate.toISOString().split('T')[0],
      'Payment Status': order.paymentStatus,
      'Shipping Status': order.shippingStatus,
      'Tracking Number': order.trackingNumber || '',
      'Items': order.orderItems.map(item => `${item.title} (${item.quantity})`).join('; '),
      'Shipping Address': JSON.stringify(JSON.parse(order.shippingAddress as string)),
    }));

    return {
      data: exportData,
      filename: `orders_export_${new Date().toISOString().split('T')[0]}.${format}`,
      count: exportData.length,
    };
  }

  async getOrderStats(accountId?: number, dateRange?: { start: Date; end: Date }) {
    const where: any = {};
    
    if (accountId) {
      where.ebayAccountId = accountId;
    }
    
    if (dateRange) {
      where.orderDate = {
        gte: dateRange.start,
        lte: dateRange.end,
      };
    }

    const [
      totalOrders,
      paidOrders,
      shippedOrders,
      revenueStats,
      topBuyers,
    ] = await Promise.all([
      prisma.order.count({ where }),
      prisma.order.count({ where: { ...where, paymentStatus: 'paid' } }),
      prisma.order.count({ where: { ...where, shippingStatus: { in: ['shipped', 'delivered'] } } }),
      prisma.order.aggregate({
        where: { ...where, paymentStatus: 'paid' },
        _sum: { totalAmount: true },
        _avg: { totalAmount: true },
      }),
      prisma.order.groupBy({
        by: ['buyerUsername'],
        where: { ...where, paymentStatus: 'paid' },
        _count: { id: true },
        _sum: { totalAmount: true },
        orderBy: { _count: { id: 'desc' } },
        take: 10,
      }),
    ]);

    return {
      totalOrders,
      paidOrders,
      shippedOrders,
      totalRevenue: revenueStats._sum.totalAmount || 0,
      averageOrderValue: revenueStats._avg.totalAmount || 0,
      conversionRate: totalOrders > 0 ? (paidOrders / totalOrders) * 100 : 0,
      fulfillmentRate: paidOrders > 0 ? (shippedOrders / paidOrders) * 100 : 0,
      topBuyers: topBuyers.map(buyer => ({
        username: buyer.buyerUsername,
        orderCount: buyer._count.id,
        totalSpent: buyer._sum.totalAmount || 0,
      })),
    };
  }
}
```

### 7. Order Controller
```typescript
// src/controllers/order.controller.ts
import { Request, Response } from 'express';
import { OrderService } from '../services/order.service';
import { OrderStatusService } from '../services/order-status.service';
import { TrackingService } from '../services/tracking.service';
import {
  orderFilterSchema,
  updateOrderStatusSchema,
  bulkUpdateOrdersSchema,
} from '../schemas/order.schema';
import { ApiResponse } from '../types/common.types';

const orderService = new OrderService();
const orderStatusService = new OrderStatusService();
const trackingService = new TrackingService();

export class OrderController {
  async getOrders(req: Request, res: Response<ApiResponse>) {
    try {
      const page = parseInt(req.query.page as string) || 1;
      const limit = parseInt(req.query.limit as string) || 20;
      const sortBy = req.query.sortBy as string || 'orderDate';
      const sortOrder = (req.query.sortOrder as 'asc' | 'desc') || 'desc';
      
      // Parse filters from query params
      const filters = orderFilterSchema.parse({
        status: req.query.status ? (req.query.status as string).split(',') : undefined,
        paymentStatus: req.query.paymentStatus ? (req.query.paymentStatus as string).split(',') : undefined,
        shippingStatus: req.query.shippingStatus ? (req.query.shippingStatus as string).split(',') : undefined,
        dateRange: req.query.startDate && req.query.endDate ? {
          start: new Date(req.query.startDate as string).toISOString(),
          end: new Date(req.query.endDate as string).toISOString(),
        } : undefined,
        buyerUsername: req.query.buyerUsername as string,
        itemNumber: req.query.itemNumber as string,
        trackingNumber: req.query.trackingNumber as string,
        minAmount: req.query.minAmount ? parseFloat(req.query.minAmount as string) : undefined,
        maxAmount: req.query.maxAmount ? parseFloat(req.query.maxAmount as string) : undefined,
      });
      
      const result = await orderService.getOrders(
        { page, limit, sortBy, sortOrder },
        filters,
        req.user?.accountIds
      );
      
      res.json({
        success: true,
        data: result.orders,
        meta: result.pagination,
      });
    } catch (error) {
      res.status(500).json({
        success: false,
        error: error instanceof Error ? error.message : 'Failed to get orders',
      });
    }
  }
  
  async getOrderById(req: Request, res: Response<ApiResponse>) {
    try {
      const orderId = parseInt(req.params.id);
      const order = await orderService.getOrderById(orderId);
      
      // Check if user has access to this order's account
      if (req.user?.role !== 'super_admin' && !req.user?.accountIds.includes(order.account.id)) {
        return res.status(403).json({
          success: false,
          error: 'Access denied to this order',
        });
      }
      
      res.json({
        success: true,
        data: order,
      });
    } catch (error) {
      res.status(404).json({
        success: false,
        error: error instanceof Error ? error.message : 'Order not found',
      });
    }
  }
  
  async updateOrderStatus(req: Request, res: Response<ApiResponse>) {
    try {
      const orderId = parseInt(req.params.id);
      const validatedData = updateOrderStatusSchema.parse(req.body);
      const userId = req.user?.userId;
      
      if (!userId) {
        return res.status(401).json({
          success: false,
          error: 'User not authenticated',
        });
      }
      
      // Check if user has access to this order
      const order = await orderService.getOrderById(orderId);
      if (req.user?.role !== 'super_admin' && !req.user?.accountIds.includes(order.account.id)) {
        return res.status(403).json({
          success: false,
          error: 'Access denied to this order',
        });
      }
      
      const updatedOrder = await orderStatusService.updateOrderStatus(
        orderId,
        validatedData,
        userId
      );
      
      res.json({
        success: true,
        data: updatedOrder,
        message: 'Order status updated successfully',
      });
    } catch (error) {
      res.status(400).json({
        success: false,
        error: error instanceof Error ? error.message : 'Failed to update order status',
      });
    }
  }
  
  async bulkUpdateOrders(req: Request, res: Response<ApiResponse>) {
    try {
      const validatedData = bulkUpdateOrdersSchema.parse(req.body);
      const userId = req.user?.userId;
      
      if (!userId) {
        return res.status(401).json({
          success: false,
          error: 'User not authenticated',
        });
      }
      
      // Verify user has access to all orders
      if (req.user?.role !== 'super_admin') {
        const orders = await prisma.order.findMany({
          where: { id: { in: validatedData.orderIds } },
          select: { id: true, ebayAccountId: true },
        });
        
        const unauthorizedOrders = orders.filter(
          order => !req.user?.accountIds.includes(order.ebayAccountId)
        );
        
        if (unauthorizedOrders.length > 0) {
          return res.status(403).json({
            success: false,
            error: `Access denied to orders: ${unauthorizedOrders.map(o => o.id).join(', ')}`,
          });
        }
      }
      
      const result = await orderStatusService.bulkUpdateOrders(
        validatedData.orderIds,
        validatedData.updates,
        userId
      );
      
      res.json({
        success: true,
        data: result,
        message: `Bulk update completed. Updated: ${result.updated}, Failed: ${result.failed}`,
      });
    } catch (error) {
      res.status(400).json({
        success: false,
        error: error instanceof Error ? error.message : 'Bulk update failed',
      });
    }
  }
  
  async getOrdersNeedingShipment(req: Request, res: Response<ApiResponse>) {
    try {
      const accountId = parseInt(req.params.accountId);
      const limit = parseInt(req.query.limit as string) || 50;
      
      // Check account access
      if (req.user?.role !== 'super_admin' && !req.user?.accountIds.includes(accountId)) {
        return res.status(403).json({
          success: false,
          error: 'Access denied to this account',
        });
      }
      
      const orders = await trackingService.getOrdersNeedingShipment(accountId, limit);
      
      res.json({
        success: true,
        data: orders,
        meta: { count: orders.length, limit },
      });
    } catch (error) {
      res.status(500).json({
        success: false,
        error: error instanceof Error ? error.message : 'Failed to get orders needing shipment',
      });
    }
  }
  
  async exportOrders(req: Request, res: Response) {
    try {
      const format = (req.query.format as 'csv' | 'excel') || 'csv';
      
      // Parse filters (same as getOrders)
      const filters = orderFilterSchema.parse({
        status: req.query.status ? (req.query.status as string).split(',') : undefined,
        paymentStatus: req.query.paymentStatus ? (req.query.paymentStatus as string).split(',') : undefined,
        shippingStatus: req.query.shippingStatus ? (req.query.shippingStatus as string).split(',') : undefined,
        dateRange: req.query.startDate && req.query.endDate ? {
          start: new Date(req.query.startDate as string).toISOString(),
          end: new Date(req.query.endDate as string).toISOString(),
        } : undefined,
        buyerUsername: req.query.buyerUsername as string,
        trackingNumber: req.query.trackingNumber as string,
        minAmount: req.query.minAmount ? parseFloat(req.query.minAmount as string) : undefined,
        maxAmount: req.query.maxAmount ? parseFloat(req.query.maxAmount as string) : undefined,
      });
      
      const result = await orderService.exportOrders(
        filters,
        req.user?.accountIds,
        format
      );
      
      // Set headers for file download
      res.setHeader('Content-Type', format === 'csv' ? 'text/csv' : 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet');
      res.setHeader('Content-Disposition', `attachment; filename="${result.filename}"`);
      
      // Convert data to CSV format (simplified)
      if (format === 'csv') {
        const headers = Object.keys(result.data[0] || {});
        const csvContent = [
          headers.join(','),
          ...result.data.map(row => 
            headers.map(header => JSON.stringify(row[header] || '')).join(',')
          ),
        ].join('\n');
        
        res.send(csvContent);
      } else {
        // For Excel format, you would use a library like xlsx
        res.json({
          success: true,
          message: 'Excel export not implemented yet',
          data: { count: result.count },
        });
      }
    } catch (error) {
      res.status(500).json({
        success: false,
        error: error instanceof Error ? error.message : 'Export failed',
      });
    }
  }
  
  async getOrderStats(req: Request, res: Response<ApiResponse>) {
    try {
      const accountId = req.query.accountId ? parseInt(req.query.accountId as string) : undefined;
      const dateRange = req.query.startDate && req.query.endDate ? {
        start: new Date(req.query.startDate as string),
        end: new Date(req.query.endDate as string),
      } : undefined;
      
      // Check account access
      if (accountId && req.user?.role !== 'super_admin' && !req.user?.accountIds.includes(accountId)) {
        return res.status(403).json({
          success: false,
          error: 'Access denied to this account',
        });
      }
      
      const stats = await orderService.getOrderStats(accountId, dateRange);
      
      res.json({
        success: true,
        data: stats,
      });
    } catch (error) {
      res.status(500).json({
        success: false,
        error: error instanceof Error ? error.message : 'Failed to get order stats',
      });
    }
  }
}
```

### 8. Tracking Controller
```typescript
// src/controllers/tracking.controller.ts
import { Request, Response } from 'express';
import { TrackingService } from '../services/tracking.service';
import { trackingUpdateSchema, bulkTrackingUploadSchema } from '../schemas/order.schema';
import { ApiResponse } from '../types/common.types';

const trackingService = new TrackingService();

export class TrackingController {
  async updateOrderTracking(req: Request, res: Response<ApiResponse>) {
    try {
      const orderId = parseInt(req.params.orderId);
      const validatedData = trackingUpdateSchema.parse(req.body);
      const userId = req.user?.userId;
      
      if (!userId) {
        return res.status(401).json({
          success: false,
          error: 'User not authenticated',
        });
      }
      
      const updatedOrder = await trackingService.updateOrderTracking(
        orderId,
        validatedData.trackingNumber,
        validatedData.carrier,
        userId
      );
      
      res.json({
        success: true,
        data: updatedOrder,
        message: 'Tracking information updated successfully',
      });
    } catch (error) {
      res.status(400).json({
        success: false,
        error: error instanceof Error ? error.message : 'Failed to update tracking',
      });
    }
  }
  
  async bulkUploadTracking(req: Request, res: Response<ApiResponse>) {
    try {
      const accountId = parseInt(req.params.accountId);
      const validatedData = bulkTrackingUploadSchema.parse(req.body);
      const userId = req.user?.userId;
      
      if (!userId) {
        return res.status(401).json({
          success: false,
          error: 'User not authenticated',
        });
      }
      
      // Check account access
      if (req.user?.role !== 'super_admin' && !req.user?.accountIds.includes(accountId)) {
        return res.status(403).json({
          success: false,
          error: 'Access denied to this account',
        });
      }
      
      const result = await trackingService.bulkUpdateTracking(
        validatedData.orders,
        accountId,
        userId
      );
      
      res.json({
        success: true,
        data: result,
        message: `Bulk tracking update completed. Updated: ${result.updated}, Failed: ${result.failed}, Not Found: ${result.notFound}`,
      });
    } catch (error) {
      res.status(400).json({
        success: false,
        error: error instanceof Error ? error.message : 'Bulk tracking update failed',
      });
    }
  }
  
  async getOrdersWithoutTracking(req: Request, res: Response<ApiResponse>) {
    try {
      const accountId = parseInt(req.params.accountId);
      const limit = parseInt(req.query.limit as string) || 50;
      
      // Check account access
      if (req.user?.role !== 'super_admin' && !req.user?.accountIds.includes(accountId)) {
        return res.status(403).json({
          success: false,
          error: 'Access denied to this account',
        });
      }
      
      const orders = await trackingService.getOrdersWithoutTracking(accountId, limit);
      
      res.json({
        success: true,
        data: orders,
        meta: { count: orders.length, limit },
      });
    } catch (error) {
      res.status(500).json({
        success: false,
        error: error instanceof Error ? error.message : 'Failed to get orders without tracking',
      });
    }
  }
  
  async getSupportedCarriers(req: Request, res: Response<ApiResponse>) {
    try {
      const carriers = trackingService.getSupportedCarriers();
      
      res.json({
        success: true,
        data: carriers,
      });
    } catch (error) {
      res.status(500).json({
        success: false,
        error: 'Failed to get supported carriers',
      });
    }
  }
  
  async getTrackingUrl(req: Request, res: Response<ApiResponse>) {
    try {
      const { trackingNumber, carrier } = req.query;
      
      if (!trackingNumber || !carrier) {
        return res.status(400).json({
          success: false,
          error: 'Tracking number and carrier are required',
        });
      }
      
      const trackingUrl = trackingService.getTrackingUrl(
        trackingNumber as string,
        carrier as string
      );
      
      if (!trackingUrl) {
        return res.status(404).json({
          success: false,
          error: 'Unsupported carrier or invalid tracking number',
        });
      }
      
      res.json({
        success: true,
        data: { trackingUrl },
      });
    } catch (error) {
      res.status(500).json({
        success: false,
        error: 'Failed to generate tracking URL',
      });
    }
  }
}
```

### 9. API Routes
```typescript
// src/routes/order.routes.ts
import { Router } from 'express';
import { OrderController } from '../controllers/order.controller';
import { authenticate, checkAccountAccess } from '../middleware/auth.middleware';

const router = Router();
const orderController = new OrderController();

// All routes require authentication
router.use(authenticate);

// Order CRUD operations
router.get('/', orderController.getOrders.bind(orderController));
router.get('/stats', orderController.getOrderStats.bind(orderController));
router.get('/export', orderController.exportOrders.bind(orderController));
router.get('/:id', orderController.getOrderById.bind(orderController));
router.put('/:id/status', orderController.updateOrderStatus.bind(orderController));
router.post('/bulk-update', orderController.bulkUpdateOrders.bind(orderController));

// Account-specific endpoints
router.get('/account/:accountId/need-shipment', checkAccountAccess, orderController.getOrdersNeedingShipment.bind(orderController));

export default router;
```

```typescript
// src/routes/tracking.routes.ts  
import { Router } from 'express';
import { TrackingController } from '../controllers/tracking.controller';
import { authenticate, checkAccountAccess } from '../middleware/auth.middleware';

const router = Router();
const trackingController = new TrackingController();

// All routes require authentication
router.use(authenticate);

// Tracking operations
router.put('/order/:orderId', trackingController.updateOrderTracking.bind(trackingController));
router.post('/account/:accountId/bulk-upload', checkAccountAccess, trackingController.bulkUploadTracking.bind(trackingController));
router.get('/account/:accountId/without-tracking', checkAccountAccess, trackingController.getOrdersWithoutTracking.bind(trackingController));
router.get('/carriers', trackingController.getSupportedCarriers.bind(trackingController));
router.get('/url', trackingController.getTrackingUrl.bind(trackingController));

export default router;
```

### 10. Database Schema Updates
```prisma
// Add to existing schema in prisma/schema.prisma

model Customer {
  id              Int      @id @default(autoincrement())
  ebayUsername    String   @unique @map("ebay_username") @db.VarChar(100)
  email           String   @map("email") @db.VarChar(255)
  fullName        String?  @map("full_name") @db.VarChar(255)
  phone           String?  @db.VarChar(50)
  address         Json?
  customerType    String   @default("new") @map("customer_type") @db.VarChar(20)
  firstOrderDate  DateTime @map("first_order_date")
  lastOrderDate   DateTime @map("last_order_date")
  totalOrders     Int      @default(0) @map("total_orders")
  totalSpent      Decimal  @default(0) @map("total_spent") @db.Decimal(10, 2)
  notes           String?
  isActive        Boolean  @default(true) @map("is_active")
  createdAt       DateTime @default(now()) @map("created_at")
  updatedAt       DateTime @updatedAt @map("updated_at")

  // Relations
  segments        CustomerSegment[]

  @@map("customers")
}

model CustomerSegment {
  id            Int      @id @default(autoincrement())
  customerId    Int      @map("customer_id")
  segmentType   String   @map("segment_type") @db.VarChar(50)
  segmentValue  String   @map("segment_value") @db.VarChar(100)
  assignedAt    DateTime @default(now()) @map("assigned_at")
  notes         String?

  // Relations
  customer      Customer @relation(fields: [customerId], references: [id], onDelete: Cascade)

  @@unique([customerId])
  @@map("customer_segments")
}

model OrderStatusHistory {
  id              Int      @id @default(autoincrement())
  orderId         Int      @map("order_id")
  statusFrom      String   @map("status_from") @db.VarChar(50)
  statusTo        String   @map("status_to") @db.VarChar(50)
  trackingNumber  String?  @map("tracking_number") @db.VarChar(100)
  notes           String?
  updatedBy       Int      @map("updated_by")
  updatedAt       DateTime @default(now()) @map("updated_at")

  // Relations
  order           Order    @relation(fields: [orderId], references: [id], onDelete: Cascade)
  updatedByUser   User     @relation(fields: [updatedBy], references: [id])

  @@map("order_status_history")
}

// Update existing Order model to include relations
model Order {
  // ... existing fields ...
  
  // Relations
  account         EbayAccount @relation(fields: [ebayAccountId], references: [id], onDelete: Cascade)
  orderItems      OrderItem[]
  statusHistory   OrderStatusHistory[]

  @@unique([ebayOrderId, ebayAccountId])
  @@map("orders")
}

// Update User model to include relation
model User {
  // ... existing fields ...
  
  // Relations
  ebayAccounts        EbayAccount[]
  accountPermissions  UserAccountPermission[]
  assignedPermissions UserAccountPermission[] @relation("AssignedBy")
  orderStatusUpdates  OrderStatusHistory[]

  @@map("users")
}

// Update EbayAccount model to include relations
model EbayAccount {
  // ... existing fields ...
  
  // Relations
  user               User     @relation(fields: [userId], references: [id], onDelete: Cascade)
  accountPermissions UserAccountPermission[]
  syncHistory        SyncHistory[]
  listings           Listing[]
  orders             Order[]

  @@map("ebay_accounts")
}
```

## Success Criteria

1. ✅ Order listing with advanced filtering
2. ✅ Order status management system  
3. ✅ Bulk order operations
4. ✅ Tracking number management
5. ✅ Customer data integration
6. ✅ Order export functionality
7. ✅ Status history tracking
8. ✅ Shipping management tools
9. ✅ Order statistics dashboard
10. ✅ Role-based access control

## Next Steps
- Plan 5: Listing Management Module
- Plan 6: Product & Supplier Management