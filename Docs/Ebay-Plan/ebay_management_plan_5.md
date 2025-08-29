# Plan 5: Listing Management Module

## Objective
Build comprehensive listing management system with performance tracking, bulk operations, draft management, and listing optimization tools.

## Dependencies
- Plan 1: Database Setup & Foundation completed
- Plan 2: Authentication & User Management APIs completed  
- Plan 3: CSV Processing Engine completed
- Plan 4: Order Management Module completed

## File Structure Updates
```
src/
├── services/
│   ├── listing.service.ts
│   ├── listing-performance.service.ts
│   ├── draft-listing.service.ts
│   └── listing-optimization.service.ts
├── controllers/
│   ├── listing.controller.ts
│   ├── draft-listing.controller.ts
│   └── listing-analytics.controller.ts
├── routes/
│   ├── listing.routes.ts
│   └── draft-listing.routes.ts
├── schemas/
│   ├── listing.schema.ts
│   └── draft-listing.schema.ts
├── types/
│   ├── listing.types.ts
│   └── performance.types.ts
├── utils/
│   ├── listing-helpers.ts
│   └── performance-calculator.ts
└── jobs/
    ├── listing-sync.job.ts
    └── performance-analysis.job.ts
```

## Implementation Files

### 1. Listing Type Definitions
```typescript
// src/types/listing.types.ts

export interface ListingFilter {
  status?: ListingStatus[];
  format?: ListingFormat[];
  categoryName?: string;
  priceRange?: {
    min: number;
    max: number;
  };
  quantityRange?: {
    min: number;
    max: number;
  };
  dateRange?: {
    start: Date;
    end: Date;
  };
  sku?: string;
  title?: string;
  hasWatchers?: boolean;
  hasSales?: boolean;
  endingSoon?: boolean; // within 24-48 hours
  lowStock?: boolean;
  performanceLevel?: PerformanceLevel[];
}

export type ListingStatus = 'active' | 'ended' | 'sold' | 'cancelled' | 'scheduled' | 'draft';
export type ListingFormat = 'FIXED_PRICE' | 'AUCTION' | 'STORE_INVENTORY';
export type PerformanceLevel = 'excellent' | 'good' | 'average' | 'poor' | 'needs_attention';

export interface ListingPerformance {
  listingId: number;
  itemNumber: number;
  views: number;
  watchers: number;
  impressions: number;
  clickThroughRate: number;
  conversionRate: number;
  averageDaysToSell: number;
  totalSales: number;
  totalRevenue: number;
  competitorCount: number;
  pricePosition: 'lowest' | 'below_average' | 'average' | 'above_average' | 'highest';
  performanceScore: number;
  performanceLevel: PerformanceLevel;
  recommendations: string[];
  lastAnalyzed: Date;
}

export interface BulkListingUpdate {
  listingIds: number[];
  updates: {
    status?: ListingStatus;
    price?: number;
    quantity?: number;
    categoryName?: string;
    condition?: string;
    title?: string;
    endDate?: Date;
  };
}

export interface DraftListing {
  id: number;
  accountId: number;
  title: string;
  description?: string;
  sku?: string;
  categoryName?: string;
  condition: string;
  startPrice: number;
  quantity: number;
  format: ListingFormat;
  duration: number; // days
  images?: string[];
  shippingProfile?: any;
  returnPolicy?: any;
  itemSpecifics?: { [key: string]: string };
  scheduledStartDate?: Date;
  status: 'draft' | 'scheduled' | 'published' | 'failed';
  createdBy: number;
  createdAt: Date;
  updatedAt: Date;
}

export interface ListingOptimizationSuggestion {
  listingId: number;
  type: 'title' | 'price' | 'category' | 'images' | 'description' | 'keywords';
  priority: 'high' | 'medium' | 'low';
  currentValue: string;
  suggestedValue: string;
  reasoning: string;
  expectedImpact: string;
  confidence: number;
}

export interface ListingSummary {
  totalListings: number;
  activeListings: number;
  endedListings: number;
  draftListings: number;
  totalValue: number;
  averagePrice: number;
  statusBreakdown: { [key in ListingStatus]: number };
  performanceBreakdown: { [key in PerformanceLevel]: number };
  topCategories: Array<{ name: string; count: number; revenue: number }>;
  endingSoon: number;
  lowStock: number;
  needsAttention: number;
}
```

### 2. Listing Schemas
```typescript
// src/schemas/listing.schema.ts
import { z } from 'zod';

export const listingFilterSchema = z.object({
  status: z.array(z.enum(['active', 'ended', 'sold', 'cancelled', 'scheduled', 'draft'])).optional(),
  format: z.array(z.enum(['FIXED_PRICE', 'AUCTION', 'STORE_INVENTORY'])).optional(),
  categoryName: z.string().max(100).optional(),
  priceRange: z.object({
    min: z.number().min(0),
    max: z.number().min(0),
  }).optional(),
  quantityRange: z.object({
    min: z.number().min(0),
    max: z.number().min(0),
  }).optional(),
  dateRange: z.object({
    start: z.string().datetime(),
    end: z.string().datetime(),
  }).optional(),
  sku: z.string().max(100).optional(),
  title: z.string().max(255).optional(),
  hasWatchers: z.boolean().optional(),
  hasSales: z.boolean().optional(),
  endingSoon: z.boolean().optional(),
  lowStock: z.boolean().optional(),
  performanceLevel: z.array(z.enum(['excellent', 'good', 'average', 'poor', 'needs_attention'])).optional(),
});

export const updateListingSchema = z.object({
  title: z.string().min(1).max(255).optional(),
  currentPrice: z.number().min(0.01).optional(),
  availableQuantity: z.number().min(0).optional(),
  condition: z.string().max(50).optional(),
  categoryName: z.string().max(100).optional(),
  listingStatus: z.enum(['active', 'ended', 'sold', 'cancelled']).optional(),
  endDate: z.string().datetime().optional(),
  notes: z.string().max(1000).optional(),
});

export const bulkUpdateListingsSchema = z.object({
  listingIds: z.array(z.number().positive()).min(1).max(100),
  updates: z.object({
    status: z.enum(['active', 'ended', 'sold', 'cancelled']).optional(),
    price: z.number().min(0.01).optional(),
    quantity: z.number().min(0).optional(),
    categoryName: z.string().max(100).optional(),
    condition: z.string().max(50).optional(),
    title: z.string().max(255).optional(),
    endDate: z.string().datetime().optional(),
  }),
});

export const createDraftListingSchema = z.object({
  title: z.string().min(1).max(255),
  description: z.string().max(5000).optional(),
  sku: z.string().max(100).optional(),
  categoryName: z.string().max(100),
  condition: z.string().max(50),
  startPrice: z.number().min(0.01),
  quantity: z.number().min(1),
  format: z.enum(['FIXED_PRICE', 'AUCTION', 'STORE_INVENTORY']),
  duration: z.number().min(1).max(30).default(7),
  images: z.array(z.string().url()).max(12).optional(),
  shippingProfile: z.any().optional(),
  returnPolicy: z.any().optional(),
  itemSpecifics: z.record(z.string(), z.string()).optional(),
  scheduledStartDate: z.string().datetime().optional(),
});

export const updateDraftListingSchema = createDraftListingSchema.partial();

export const listingAnalyticsSchema = z.object({
  accountId: z.number().positive().optional(),
  dateRange: z.object({
    start: z.string().datetime(),
    end: z.string().datetime(),
  }).optional(),
  groupBy: z.enum(['day', 'week', 'month', 'category', 'format']).default('day'),
  metrics: z.array(z.enum(['views', 'watchers', 'sales', 'revenue', 'conversion_rate'])).optional(),
});

export type ListingFilterInput = z.infer<typeof listingFilterSchema>;
export type UpdateListingInput = z.infer<typeof updateListingSchema>;
export type BulkUpdateListingsInput = z.infer<typeof bulkUpdateListingsSchema>;
export type CreateDraftListingInput = z.infer<typeof createDraftListingSchema>;
export type UpdateDraftListingInput = z.infer<typeof updateDraftListingSchema>;
export type ListingAnalyticsInput = z.infer<typeof listingAnalyticsSchema>;
```

### 3. Listing Service
```typescript
// src/services/listing.service.ts
import { prisma } from '../config/database';
import { ListingFilter, BulkListingUpdate } from '../types/listing.types';
import { PaginationParams } from '../types/common.types';

export class ListingService {
  async getListings(
    pagination: PaginationParams,
    filters: ListingFilter,
    accountIds?: number[]
  ) {
    const { page = 1, limit = 20, sortBy = 'createdAt', sortOrder = 'desc' } = pagination;
    const skip = (page - 1) * limit;
    
    const where: any = {};
    
    if (accountIds && accountIds.length > 0) {
      where.ebayAccountId = { in: accountIds };
    }
    
    if (filters.status && filters.status.length > 0) {
      where.listingStatus = { in: filters.status };
    }
    
    if (filters.format && filters.format.length > 0) {
      where.format = { in: filters.format };
    }
    
    if (filters.categoryName) {
      where.categoryName = {
        contains: filters.categoryName,
        mode: 'insensitive',
      };
    }
    
    if (filters.priceRange) {
      where.currentPrice = {
        gte: filters.priceRange.min,
        lte: filters.priceRange.max,
      };
    }
    
    if (filters.quantityRange) {
      where.availableQuantity = {
        gte: filters.quantityRange.min,
        lte: filters.quantityRange.max,
      };
    }
    
    if (filters.dateRange) {
      where.createdAt = {
        gte: filters.dateRange.start,
        lte: filters.dateRange.end,
      };
    }
    
    if (filters.sku) {
      where.sku = {
        contains: filters.sku,
        mode: 'insensitive',
      };
    }
    
    if (filters.title) {
      where.title = {
        contains: filters.title,
        mode: 'insensitive',
      };
    }
    
    if (filters.hasWatchers) {
      where.watchers = { gt: 0 };
    }
    
    if (filters.hasSales) {
      where.soldQuantity = { gt: 0 };
    }
    
    if (filters.endingSoon) {
      const tomorrow = new Date();
      tomorrow.setDate(tomorrow.getDate() + 1);
      where.endDate = { lte: tomorrow };
      where.listingStatus = 'active';
    }
    
    if (filters.lowStock) {
      where.availableQuantity = { lte: 5 };
      where.listingStatus = 'active';
    }

    const [listings, total] = await Promise.all([
      prisma.listing.findMany({
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
              quantity: true,
              unitPrice: true,
              order: {
                select: {
                  orderDate: true,
                  paymentStatus: true,
                },
              },
            },
          },
          _count: {
            select: {
              orderItems: true,
            },
          },
        },
      }),
      prisma.listing.count({ where }),
    ]);

    return {
      listings: listings.map(listing => ({
        ...listing,
        salesCount: listing._count.orderItems,
        totalRevenue: listing.orderItems.reduce((sum, item) => 
          sum + (Number(item.unitPrice) * item.quantity), 0
        ),
        lastSaleDate: listing.orderItems.length > 0 
          ? listing.orderItems
              .map(item => item.order.orderDate)
              .sort((a, b) => b.getTime() - a.getTime())[0]
          : null,
        _count: undefined,
        orderItems: undefined,
      })),
      pagination: {
        page,
        limit,
        total,
        totalPages: Math.ceil(total / limit),
      },
    };
  }

  async getListingById(listingId: number) {
    const listing = await prisma.listing.findUnique({
      where: { id: listingId },
      include: {
        account: {
          select: {
            id: true,
            accountName: true,
            accountEmail: true,
          },
        },
        orderItems: {
          include: {
            order: {
              select: {
                ebayOrderId: true,
                buyerUsername: true,
                orderDate: true,
                totalAmount: true,
                paymentStatus: true,
                shippingStatus: true,
              },
            },
          },
          orderBy: {
            order: { orderDate: 'desc' },
          },
        },
      },
    });

    if (!listing) {
      throw new Error('Listing not found');
    }

    const salesHistory = listing.orderItems.map(item => ({
      orderId: item.order.ebayOrderId,
      buyer: item.order.buyerUsername,
      quantity: item.quantity,
      price: item.unitPrice,
      date: item.order.orderDate,
      status: item.order.paymentStatus,
    }));

    return {
      ...listing,
      salesHistory,
      totalSales: listing.orderItems.reduce((sum, item) => sum + item.quantity, 0),
      totalRevenue: listing.orderItems.reduce((sum, item) => 
        sum + (Number(item.unitPrice) * item.quantity), 0
      ),
      orderItems: undefined,
    };
  }

  async updateListing(listingId: number, updates: any, updatedBy: number) {
    // Create listing history entry
    const originalListing = await prisma.listing.findUnique({
      where: { id: listingId },
    });

    if (!originalListing) {
      throw new Error('Listing not found');
    }

    const updatedListing = await prisma.listing.update({
      where: { id: listingId },
      data: {
        ...updates,
        updatedAt: new Date(),
      },
    });

    // Track significant changes
    const significantChanges = ['currentPrice', 'availableQuantity', 'listingStatus', 'title'];
    const changes = significantChanges.filter(field => 
      updates[field] !== undefined && updates[field] !== originalListing[field as keyof typeof originalListing]
    );

    if (changes.length > 0) {
      await prisma.listingHistory.create({
        data: {
          listingId,
          changes: JSON.stringify(
            changes.reduce((obj, field) => ({
              ...obj,
              [field]: {
                from: originalListing[field as keyof typeof originalListing],
                to: updates[field],
              },
            }), {})
          ),
          updatedBy,
        },
      });
    }

    return updatedListing;
  }

  async bulkUpdateListings(
    listingIds: number[],
    updates: any,
    updatedBy: number
  ) {
    const results = {
      updated: 0,
      failed: 0,
      errors: [] as string[],
    };

    // Process in batches to avoid overwhelming the database
    const batchSize = 20;
    for (let i = 0; i < listingIds.length; i += batchSize) {
      const batch = listingIds.slice(i, i + batchSize);
      
      const promises = batch.map(async (listingId) => {
        try {
          await this.updateListing(listingId, updates, updatedBy);
          results.updated++;
        } catch (error) {
          results.failed++;
          results.errors.push(`Listing ${listingId}: ${error instanceof Error ? error.message : 'Unknown error'}`);
        }
      });

      await Promise.all(promises);
    }

    return results;
  }

  async getListingSummary(accountId?: number, dateRange?: { start: Date; end: Date }) {
    const where: any = {};
    
    if (accountId) {
      where.ebayAccountId = accountId;
    }
    
    if (dateRange) {
      where.createdAt = {
        gte: dateRange.start,
        lte: dateRange.end,
      };
    }

    const [
      totalListings,
      statusBreakdown,
      formatBreakdown,
      priceStats,
      topCategories,
      endingSoon,
      lowStock,
      needsAttention,
    ] = await Promise.all([
      prisma.listing.count({ where }),
      prisma.listing.groupBy({
        by: ['listingStatus'],
        where,
        _count: { id: true },
      }),
      prisma.listing.groupBy({
        by: ['format'],
        where,
        _count: { id: true },
      }),
      prisma.listing.aggregate({
        where,
        _sum: { currentPrice: true, availableQuantity: true },
        _avg: { currentPrice: true },
      }),
      prisma.listing.groupBy({
        by: ['categoryName'],
        where,
        _count: { id: true },
        _sum: { currentPrice: true },
        orderBy: { _count: { id: 'desc' } },
        take: 10,
      }),
      prisma.listing.count({
        where: {
          ...where,
          listingStatus: 'active',
          endDate: { lte: new Date(Date.now() + 24 * 60 * 60 * 1000) },
        },
      }),
      prisma.listing.count({
        where: {
          ...where,
          listingStatus: 'active',
          availableQuantity: { lte: 5 },
        },
      }),
      prisma.listing.count({
        where: {
          ...where,
          OR: [
            { watchers: 0, soldQuantity: 0, listingStatus: 'active' },
            { availableQuantity: { lte: 2 }, listingStatus: 'active' },
          ],
        },
      }),
    ]);

    return {
      totalListings,
      activeListings: statusBreakdown.find(s => s.listingStatus === 'active')?._count.id || 0,
      endedListings: statusBreakdown.find(s => s.listingStatus === 'ended')?._count.id || 0,
      totalValue: Number(priceStats._sum.currentPrice) || 0,
      averagePrice: Number(priceStats._avg.currentPrice) || 0,
      statusBreakdown: this.formatBreakdown(statusBreakdown),
      formatBreakdown: this.formatBreakdown(formatBreakdown),
      topCategories: topCategories.map(cat => ({
        name: cat.categoryName || 'Uncategorized',
        count: cat._count.id,
        revenue: Number(cat._sum.currentPrice) || 0,
      })),
      endingSoon,
      lowStock,
      needsAttention,
    };
  }

  private formatBreakdown(data: any[]) {
    const result: any = {};
    data.forEach(item => {
      const key = item.listingStatus || item.format;
      result[key] = item._count.id;
    });
    return result;
  }

  async getListingsByCategory(accountId?: number) {
    const where: any = {};
    if (accountId) {
      where.ebayAccountId = accountId;
    }

    const categories = await prisma.listing.groupBy({
      by: ['categoryName'],
      where,
      _count: { id: true },
      _sum: { 
        currentPrice: true,
        availableQuantity: true,
        soldQuantity: true,
      },
      _avg: { currentPrice: true },
      orderBy: { _count: { id: 'desc' } },
    });

    return categories.map(category => ({
      name: category.categoryName || 'Uncategorized',
      listingCount: category._count.id,
      totalValue: Number(category._sum.currentPrice) || 0,
      totalQuantity: category._sum.availableQuantity || 0,
      totalSold: category._sum.soldQuantity || 0,
      averagePrice: Number(category._avg.currentPrice) || 0,
    }));
  }

  async getEndingSoonListings(accountId: number, hours: number = 24) {
    const endTime = new Date(Date.now() + hours * 60 * 60 * 1000);
    
    const listings = await prisma.listing.findMany({
      where: {
        ebayAccountId: accountId,
        listingStatus: 'active',
        endDate: { lte: endTime },
      },
      select: {
        id: true,
        itemNumber: true,
        title: true,
        currentPrice: true,
        availableQuantity: true,
        watchers: true,
        soldQuantity: true,
        endDate: true,
      },
      orderBy: { endDate: 'asc' },
    });

    return listings.map(listing => ({
      ...listing,
      hoursRemaining: Math.max(0, Math.floor((listing.endDate.getTime() - Date.now()) / (1000 * 60 * 60))),
      hasActivity: listing.watchers > 0 || listing.soldQuantity > 0,
    }));
  }

  async searchListings(
    query: string, 
    accountIds?: number[], 
    limit: number = 20
  ) {
    const where: any = {
      OR: [
        { title: { contains: query, mode: 'insensitive' } },
        { sku: { contains: query, mode: 'insensitive' } },
        { categoryName: { contains: query, mode: 'insensitive' } },
        { itemNumber: { equals: parseInt(query) || 0 } },
      ],
    };

    if (accountIds && accountIds.length > 0) {
      where.ebayAccountId = { in: accountIds };
    }

    const listings = await prisma.listing.findMany({
      where,
      select: {
        id: true,
        itemNumber: true,
        title: true,
        sku: true,
        currentPrice: true,
        availableQuantity: true,
        listingStatus: true,
        categoryName: true,
        account: {
          select: { accountName: true },
        },
      },
      take: limit,
      orderBy: [
        { listingStatus: 'asc' }, // Active listings first
        { watchers: 'desc' },
        { soldQuantity: 'desc' },
      ],
    });

    return listings;
  }

  async exportListings(filters: ListingFilter, accountIds?: number[], format: 'csv' | 'excel' = 'csv') {
    const where: any = {};
    
    if (accountIds && accountIds.length > 0) {
      where.ebayAccountId = { in: accountIds };
    }
    
    // Apply filters (simplified for brevity)
    if (filters.status && filters.status.length > 0) {
      where.listingStatus = { in: filters.status };
    }

    const listings = await prisma.listing.findMany({
      where,
      include: {
        account: { select: { accountName: true } },
        _count: { select: { orderItems: true } },
      },
      orderBy: { createdAt: 'desc' },
    });

    const exportData = listings.map(listing => ({
      'Item Number': listing.itemNumber,
      'Account': listing.account.accountName,
      'Title': listing.title,
      'SKU': listing.sku || '',
      'Category': listing.categoryName,
      'Current Price': listing.currentPrice,
      'Available Quantity': listing.availableQuantity,
      'Sold Quantity': listing.soldQuantity,
      'Format': listing.format,
      'Condition': listing.condition,
      'Status': listing.listingStatus,
      'Watchers': listing.watchers,
      'Start Date': listing.startDate.toISOString().split('T')[0],
      'End Date': listing.endDate.toISOString().split('T')[0],
      'Sales Count': listing._count.orderItems,
      'Days Listed': Math.floor((new Date().getTime() - listing.startDate.getTime()) / (1000 * 60 * 60 * 24)),
    }));

    return {
      data: exportData,
      filename: `listings_export_${new Date().toISOString().split('T')[0]}.${format}`,
      count: exportData.length,
    };
  }
}
```

### 4. Draft Listing Service
```typescript
// src/services/draft-listing.service.ts
import { prisma } from '../config/database';
import { CreateDraftListingInput, UpdateDraftListingInput } from '../schemas/listing.schema';
import { PaginationParams, FilterParams } from '../types/common.types';

export class DraftListingService {
  async createDraftListing(data: CreateDraftListingInput, accountId: number, createdBy: number) {
    const draftListing = await prisma.draftListing.create({
      data: {
        accountId,
        title: data.title,
        description: data.description,
        sku: data.sku,
        categoryName: data.categoryName,
        condition: data.condition,
        startPrice: data.startPrice,
        quantity: data.quantity,
        format: data.format,
        duration: data.duration,
        images: data.images ? JSON.stringify(data.images) : null,
        shippingProfile: data.shippingProfile ? JSON.stringify(data.shippingProfile) : null,
        returnPolicy: data.returnPolicy ? JSON.stringify(data.returnPolicy) : null,
        itemSpecifics: data.itemSpecifics ? JSON.stringify(data.itemSpecifics) : null,
        scheduledStartDate: data.scheduledStartDate ? new Date(data.scheduledStartDate) : null,
        status: data.scheduledStartDate ? 'scheduled' : 'draft',
        createdBy,
      },
    });

    return draftListing;
  }

  async getDraftListings(
    pagination: PaginationParams,
    filters: FilterParams & { status?: string },
    accountIds?: number[]
  ) {
    const { page = 1, limit = 20, sortBy = 'updatedAt', sortOrder = 'desc' } = pagination;
    const { search, status } = filters;
    
    const skip = (page - 1) * limit;
    const where: any = {};

    if (accountIds && accountIds.length > 0) {
      where.accountId = { in: accountIds };
    }

    if (search) {
      where.OR = [
        { title: { contains: search, mode: 'insensitive' } },
        { sku: { contains: search, mode: 'insensitive' } },
        { categoryName: { contains: search, mode: 'insensitive' } },
      ];
    }

    if (status) {
      where.status = status;
    }

    const [draftListings, total] = await Promise.all([
      prisma.draftListing.findMany({
        where,
        skip,
        take: limit,
        orderBy: { [sortBy]: sortOrder },
        include: {
          account: {
            select: {
              accountName: true,
            },
          },
          createdByUser: {
            select: {
              username: true,
              fullName: true,
            },
          },
        },
      }),
      prisma.draftListing.count({ where }),
    ]);

    return {
      draftListings: draftListings.map(draft => ({
        ...draft,
        images: draft.images ? JSON.parse(draft.images) : [],
        shippingProfile: draft.shippingProfile ? JSON.parse(draft.shippingProfile) : null,
        returnPolicy: draft.returnPolicy ? JSON.parse(draft.returnPolicy) : null,
        itemSpecifics: draft.itemSpecifics ? JSON.parse(draft.itemSpecifics) : null,
      })),
      pagination: {
        page,
        limit,
        total,
        totalPages: Math.ceil(total / limit),
      },
    };
  }

  async getDraftListingById(draftId: number) {
    const draftListing = await prisma.draftListing.findUnique({
      where: { id: draftId },
      include: {
        account: {
          select: {
            id: true,
            accountName: true,
          },
        },
        createdByUser: {
          select: {
            username: true,
            fullName: true,
          },
        },
      },
    });

    if (!draftListing) {
      throw new Error('Draft listing not found');
    }

    return {
      ...draftListing,
      images: draftListing.images ? JSON.parse(draftListing.images) : [],
      shippingProfile: draftListing.shippingProfile ? JSON.parse(draftListing.shippingProfile) : null,
      returnPolicy: draftListing.returnPolicy ? JSON.parse(draftListing.returnPolicy) : null,
      itemSpecifics: draftListing.itemSpecifics ? JSON.parse(draftListing.itemSpecifics) : null,
    };
  }

  async updateDraftListing(draftId: number, data: UpdateDraftListingInput, updatedBy: number) {
    const updateData: any = { ...data };
    
    if (data.images) {
      updateData.images = JSON.stringify(data.images);
    }
    
    if (data.shippingProfile) {
      updateData.shippingProfile = JSON.stringify(data.shippingProfile);
    }
    
    if (data.returnPolicy) {
      updateData.returnPolicy = JSON.stringify(data.returnPolicy);
    }
    
    if (data.itemSpecifics) {
      updateData.itemSpecifics = JSON.stringify(data.itemSpecifics);
    }
    
    if (data.scheduledStartDate) {
      updateData.scheduledStartDate = new Date(data.scheduledStartDate);
      updateData.status = 'scheduled';
    }

    const updatedDraft = await prisma.draftListing.update({
      where: { id: draftId },
      data: updateData,
    });

    return updatedDraft;
  }

  async duplicateDraftListing(draftId: number, createdBy: number) {
    const originalDraft = await this.getDraftListingById(draftId);
    
    const duplicateData = {
      title: `Copy of ${originalDraft.title}`,
      description: originalDraft.description,
      sku: originalDraft.sku,
      categoryName: originalDraft.categoryName,
      condition: originalDraft.condition,
      startPrice: originalDraft.startPrice,
      quantity: originalDraft.quantity,
      format: originalDraft.format,
      duration: originalDraft.duration,
      images: originalDraft.images,
      shippingProfile: originalDraft.shippingProfile,
      returnPolicy: originalDraft.returnPolicy,
      itemSpecifics: originalDraft.itemSpecifics,
    };

    return this.createDraftListing(duplicateData, originalDraft.account.id, createdBy);
  }

  async bulkCreateFromTemplate(
    templateId: number,
    variations: Array<{
      title: string;
      sku?: string;
      startPrice: number;
      quantity: number;
      itemSpecifics?: { [key: string]: string };
    }>,
    accountId: number,
    createdBy: number
  ) {
    const template = await this.getDraftListingById(templateId);
    const results = {
      created: 0,
      failed: 0,
      errors: [] as string[],
    };

    for (const variation of variations) {
      try {
        const draftData = {
          ...template,
          title: variation.title,
          sku: variation.sku,
          startPrice: variation.startPrice,
          quantity: variation.quantity,
          itemSpecifics: variation.itemSpecifics || template.itemSpecifics,
        };

        await this.createDraftListing(draftData, accountId, createdBy);
        results.created++;
      } catch (error) {
        results.failed++;
        results.errors.push(`${variation.title}: ${error instanceof Error ? error.message : 'Unknown error'}`);
      }
    }

    return results;
  }

  async getScheduledListings(accountId?: number) {
    const where: any = {
      status: 'scheduled',
      scheduledStartDate: { not: null },
    };

    if (accountId) {
      where.accountId = accountId;
    }

    const scheduledListings = await prisma.draftListing.findMany({
      where,
      include: {
        account: {
          select: {
            accountName: true,
          },
        },
      },
      orderBy: { scheduledStartDate: 'asc' },
    });

    return scheduledListings.map(listing => ({
      ...listing,
      images: listing.images ? JSON.parse(listing.images) : [],
      daysUntilStart: listing.scheduledStartDate 
        ? Math.ceil((listing.scheduledStartDate.getTime() - Date.now()) / (1000 * 60 * 60 * 24))
        : null,
    }));
  }

  async deleteDraftListing(draftId: number) {
    const draftListing = await prisma.draftListing.findUnique({
      where: { id: draftId },
    });

    if (!draftListing) {
      throw new Error('Draft listing not found');
    }

    if (draftListing.status === 'published') {
      throw new Error('Cannot delete published draft listing');
    }

    await prisma.draftListing.delete({
      where: { id: draftId },
    });

    return { success: true };
  }

  async markAsPublished(draftId: number, ebayItemNumber: number) {
    await prisma.draftListing.update({
      where: { id: draftId },
      data: {
        status: 'published',
        publishedItemNumber: ebayItemNumber,
        publishedAt: new Date(),
      },
    });

    return { success: true };
  }

  async getDraftStatistics(accountId?: number) {
    const where: any = {};
    if (accountId) {
      where.accountId = accountId;
    }

    const [
      totalDrafts,
      statusBreakdown,
      scheduledCount,
      avgPrice,
    ] = await Promise.all([
      prisma.draftListing.count({ where }),
      prisma.draftListing.groupBy({
        by: ['status'],
        where,
        _count: { id: true },
      }),
      prisma.draftListing.count({
        where: {
          ...where,
          status: 'scheduled',
          scheduledStartDate: { gte: new Date() },
        },
      }),
      prisma.draftListing.aggregate({
        where,
        _avg: { startPrice: true },
      }),
    ]);

    return {
      totalDrafts,
      statusBreakdown: this.formatBreakdown(statusBreakdown),
      scheduledCount,
      averagePrice: Number(avgPrice._avg.startPrice) || 0,
    };
  }

  private formatBreakdown(data: any[]) {
    const result: any = {};
    data.forEach(item => {
      result[item.status] = item._count.id;
    });
    return result;
  }
}
```

### 5. Listing Performance Service
```typescript
// src/services/listing-performance.service.ts
import { prisma } from '../config/database';
import { ListingPerformance, PerformanceLevel, ListingOptimizationSuggestion } from '../types/listing.types';

export class ListingPerformanceService {
  async analyzeListingPerformance(listingId: number): Promise<ListingPerformance> {
    const listing = await prisma.listing.findUnique({
      where: { id: listingId },
      include: {
        orderItems: {
          include: {
            order: {
              select: {
                orderDate: true,
                paymentStatus: true,
              },
            },
          },
        },
      },
    });

    if (!listing) {
      throw new Error('Listing not found');
    }

    // Calculate performance metrics
    const daysListed = Math.max(1, Math.floor(
      (new Date().getTime() - listing.startDate.getTime()) / (1000 * 60 * 60 * 24)
    ));
    
    const totalSales = listing.orderItems.reduce((sum, item) => sum + item.quantity, 0);
    const totalRevenue = listing.orderItems.reduce((sum, item) => 
      sum + (Number(item.unitPrice) * item.quantity), 0
    );
    
    const paidSales = listing.orderItems.filter(item => 
      item.order.paymentStatus === 'paid'
    );
    
    const averageDaysToSell = paidSales.length > 0
      ? paidSales.reduce((sum, item) => {
          const daysToSell = Math.floor(
            (item.order.orderDate.getTime() - listing.startDate.getTime()) / (1000 * 60 * 60 * 24)
          );
          return sum + daysToSell;
        }, 0) / paidSales.length
      : daysListed;

    // Estimate views and conversion rate based on watchers and sales
    const estimatedViews = Math.max(
      listing.watchers * 10, // Assume 10 views per watcher
      totalSales * 20, // Assume 20 views per sale
      50 // Minimum estimate
    );
    
    const conversionRate = estimatedViews > 0 ? (totalSales / estimatedViews) * 100 : 0;
    const clickThroughRate = listing.watchers / Math.max(estimatedViews / 5, 1) * 100;

    // Calculate performance score (0-100)
    let performanceScore = 0;
    
    // Sales performance (40%)
    const salesPerDay = totalSales / daysListed;
    performanceScore += Math.min(salesPerDay * 20, 40);
    
    // Conversion rate (30%)
    performanceScore += Math.min(conversionRate * 3, 30);
    
    // Engagement (20%)
    const watchersPerDay = listing.watchers / daysListed;
    performanceScore += Math.min(watchersPerDay * 10, 20);
    
    // Pricing competitiveness (10%)
    // This would require competitor data, simplified here
    performanceScore += 10;

    // Determine performance level
    let performanceLevel: PerformanceLevel;
    if (performanceScore >= 80) performanceLevel = 'excellent';
    else if (performanceScore >= 60) performanceLevel = 'good';
    else if (performanceScore >= 40) performanceLevel = 'average';
    else if (performanceScore >= 20) performanceLevel = 'poor';
    else performanceLevel = 'needs_attention';

    // Generate recommendations
    const recommendations = this.generateRecommendations(listing, {
      performanceScore,
      salesPerDay,
      conversionRate,
      watchersPerDay,
      daysListed,
    });

    return {
      listingId,
      itemNumber: Number(listing.itemNumber),
      views: estimatedViews,
      watchers: listing.watchers,
      impressions: Math.round(estimatedViews * 1.5), // Estimate
      clickThroughRate,
      conversionRate,
      averageDaysToSell,
      totalSales,
      totalRevenue,
      competitorCount: 0, // Would need competitor analysis
      pricePosition: 'average', // Simplified
      performanceScore: Math.round(performanceScore),
      performanceLevel,
      recommendations,
      lastAnalyzed: new Date(),
    };
  }

  private generateRecommendations(
    listing: any,
    metrics: {
      performanceScore: number;
      salesPerDay: number;
      conversionRate: number;
      watchersPerDay: number;
      daysListed: number;
    }
  ): string[] {
    const recommendations: string[] = [];

    if (metrics.salesPerDay < 0.1 && metrics.daysListed > 7) {
      recommendations.push("Consider reviewing and optimizing your title with better keywords");
      recommendations.push("Your listing may be priced too high - research competitor pricing");
    }

    if (listing.watchers === 0 && metrics.daysListed > 3) {
      recommendations.push("Add more high-quality photos to increase engagement");
      recommendations.push("Improve your listing description with more details and benefits");
    }

    if (metrics.conversionRate < 2 && listing.watchers > 0) {
      recommendations.push("Consider lowering your price to convert watchers to buyers");
      recommendations.push("Add a 'Best Offer' option to encourage purchases");
    }

    if (listing.availableQuantity <= 2 && listing.soldQuantity > 0) {
      recommendations.push("Consider restocking this item - it's showing good sales performance");
    }

    if (metrics.daysListed > 15 && metrics.salesPerDay < 0.05) {
      recommendations.push("Consider ending and relisting with improvements");
      recommendations.push("Try a different category or listing format");
    }

    if (listing.endDate && listing.endDate < new Date(Date.now() + 3 * 24 * 60 * 60 * 1000)) {
      recommendations.push("Listing is ending soon - consider renewing if it has watchers");
    }

    return recommendations;
  }

  async getPerformanceAnalytics(
    accountId?: number,
    dateRange?: { start: Date; end: Date }
  ) {
    const where: any = {};
    
    if (accountId) {
      where.ebayAccountId = accountId;
    }
    
    if (dateRange) {
      where.createdAt = {
        gte: dateRange.start,
        lte: dateRange.end,
      };
    }

    // Get top and bottom performers
    const [topPerformers, bottomPerformers, categoryPerformance] = await Promise.all([
      prisma.listing.findMany({
        where: { 
          ...where,
          soldQuantity: { gt: 0 },
        },
        select: {
          id: true,
          itemNumber: true,
          title: true,
          currentPrice: true,
          soldQuantity: true,
          watchers: true,
          startDate: true,
        },
        orderBy: [
          { soldQuantity: 'desc' },
          { watchers: 'desc' },
        ],
        take: 10,
      }),
      prisma.listing.findMany({
        where: {
          ...where,
          soldQuantity: 0,
          watchers: { lte: 1 },
          startDate: { lte: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000) },
        },
        select: {
          id: true,
          itemNumber: true,
          title: true,
          currentPrice: true,
          soldQuantity: true,
          watchers: true,
          startDate: true,
        },
        orderBy: { startDate: 'asc' },
        take: 10,
      }),
      prisma.listing.groupBy({
        by: ['categoryName'],
        where,
        _count: { id: true },
        _sum: { soldQuantity: true, watchers: true },
        _avg: { currentPrice: true },
        orderBy: { _sum: { soldQuantity: 'desc' } },
        take: 10,
      }),
    ]);

    return {
      topPerformers: topPerformers.map(listing => ({
        ...listing,
        daysListed: Math.floor((new Date().getTime() - listing.startDate.getTime()) / (1000 * 60 * 60 * 24)),
        salesPerDay: listing.soldQuantity / Math.max(1, Math.floor((new Date().getTime() - listing.startDate.getTime()) / (1000 * 60 * 60 * 24))),
      })),
      bottomPerformers: bottomPerformers.map(listing => ({
        ...listing,
        daysListed: Math.floor((new Date().getTime() - listing.startDate.getTime()) / (1000 * 60 * 60 * 24)),
      })),
      categoryPerformance: categoryPerformance.map(category => ({
        name: category.categoryName || 'Uncategorized',
        listingCount: category._count.id,
        totalSales: category._sum.soldQuantity || 0,
        totalWatchers: category._sum.watchers || 0,
        averagePrice: Number(category._avg.currentPrice) || 0,
        averageSalesPerListing: (category._sum.soldQuantity || 0) / category._count.id,
      })),
    };
  }

  async generateOptimizationSuggestions(listingId: number): Promise<ListingOptimizationSuggestion[]> {
    const listing = await prisma.listing.findUnique({
      where: { id: listingId },
      include: {
        orderItems: {
          select: {
            unitPrice: true,
            quantity: true,
          },
        },
      },
    });

    if (!listing) {
      throw new Error('Listing not found');
    }

    const suggestions: ListingOptimizationSuggestion[] = [];
    
    // Title optimization
    if (listing.title.length < 50) {
      suggestions.push({
        listingId,
        type: 'title',
        priority: 'high',
        currentValue: listing.title,
        suggestedValue: `${listing.title} - Add more descriptive keywords`,
        reasoning: 'Title is too short. Longer, keyword-rich titles improve search visibility.',
        expectedImpact: 'Increase visibility by 20-30%',
        confidence: 85,
      });
    }

    // Price optimization
    if (listing.watchers > 3 && listing.soldQuantity === 0) {
      const suggestedPrice = Number(listing.currentPrice) * 0.9;
      suggestions.push({
        listingId,
        type: 'price',
        priority: 'medium',
        currentValue: listing.currentPrice.toString(),
        suggestedValue: suggestedPrice.toFixed(2),
        reasoning: 'High watcher count but no sales suggests price may be too high.',
        expectedImpact: 'Increase conversion rate by 15-25%',
        confidence: 75,
      });
    }

    // Low stock alert
    if (listing.availableQuantity <= 3 && listing.soldQuantity > 0) {
      suggestions.push({
        listingId,
        type: 'quantity',
        priority: 'high',
        currentValue: listing.availableQuantity.toString(),
        suggestedValue: 'Restock to 10+ units',
        reasoning: 'Item is selling but running low on stock.',
        expectedImpact: 'Prevent lost sales',
        confidence: 95,
      });
    }

    return suggestions;
  }
}
```

### 6. Controllers Implementation
```typescript
// src/controllers/listing.controller.ts
import { Request, Response } from 'express';
import { ListingService } from '../services/listing.service';
import { ListingPerformanceService } from '../services/listing-performance.service';
import {
  listingFilterSchema,
  updateListingSchema,
  bulkUpdateListingsSchema,
} from '../schemas/listing.schema';
import { ApiResponse } from '../types/common.types';

const listingService = new ListingService();
const performanceService = new ListingPerformanceService();

export class ListingController {
  async getListings(req: Request, res: Response<ApiResponse>) {
    try {
      const page = parseInt(req.query.page as string) || 1;
      const limit = parseInt(req.query.limit as string) || 20;
      const sortBy = req.query.sortBy as string || 'createdAt';
      const sortOrder = (req.query.sortOrder as 'asc' | 'desc') || 'desc';
      
      const filters = listingFilterSchema.parse({
        status: req.query.status ? (req.query.status as string).split(',') : undefined,
        format: req.query.format ? (req.query.format as string).split(',') : undefined,
        categoryName: req.query.categoryName as string,
        priceRange: req.query.minPrice && req.query.maxPrice ? {
          min: parseFloat(req.query.minPrice as string),
          max: parseFloat(req.query.maxPrice as string),
        } : undefined,
        quantityRange: req.query.minQuantity && req.query.maxQuantity ? {
          min: parseInt(req.query.minQuantity as string),
          max: parseInt(req.query.maxQuantity as string),
        } : undefined,
        dateRange: req.query.startDate && req.query.endDate ? {
          start: new Date(req.query.startDate as string).toISOString(),
          end: new Date(req.query.endDate as string).toISOString(),
        } : undefined,
        sku: req.query.sku as string,
        title: req.query.title as string,
        hasWatchers: req.query.hasWatchers === 'true',
        hasSales: req.query.hasSales === 'true',
        endingSoon: req.query.endingSoon === 'true',
        lowStock: req.query.lowStock === 'true',
        performanceLevel: req.query.performanceLevel ? (req.query.performanceLevel as string).split(',') : undefined,
      });
      
      const result = await listingService.getListings(
        { page, limit, sortBy, sortOrder },
        filters,
        req.user?.accountIds
      );
      
      res.json({
        success: true,
        data: result.listings,
        meta: result.pagination,
      });
    } catch (error) {
      res.status(500).json({
        success: false,
        error: error instanceof Error ? error.message : 'Failed to get listings',
      });
    }
  }

  async getListingById(req: Request, res: Response<ApiResponse>) {
    try {
      const listingId = parseInt(req.params.id);
      const listing = await listingService.getListingById(listingId);
      
      // Check if user has access to this listing's account
      if (req.user?.role !== 'super_admin' && !req.user?.accountIds.includes(listing.account.id)) {
        return res.status(403).json({
          success: false,
          error: 'Access denied to this listing',
        });
      }
      
      res.json({
        success: true,
        data: listing,
      });
    } catch (error) {
      res.status(404).json({
        success: false,
        error: error instanceof Error ? error.message : 'Listing not found',
      });
    }
  }

  async updateListing(req: Request, res: Response<ApiResponse>) {
    try {
      const listingId = parseInt(req.params.id);
      const validatedData = updateListingSchema.parse(req.body);
      const userId = req.user?.userId;
      
      if (!userId) {
        return res.status(401).json({
          success: false,
          error: 'User not authenticated',
        });
      }
      
      // Check access
      const listing = await listingService.getListingById(listingId);
      if (req.user?.role !== 'super_admin' && !req.user?.accountIds.includes(listing.account.id)) {
        return res.status(403).json({
          success: false,
          error: 'Access denied to this listing',
        });
      }
      
      const updatedListing = await listingService.updateListing(
        listingId,
        validatedData,
        userId
      );
      
      res.json({
        success: true,
        data: updatedListing,
        message: 'Listing updated successfully',
      });
    } catch (error) {
      res.status(400).json({
        success: false,
        error: error instanceof Error ? error.message : 'Failed to update listing',
      });
    }
  }

  async bulkUpdateListings(req: Request, res: Response<ApiResponse>) {
    try {
      const validatedData = bulkUpdateListingsSchema.parse(req.body);
      const userId = req.user?.userId;
      
      if (!userId) {
        return res.status(401).json({
          success: false,
          error: 'User not authenticated',
        });
      }
      
      // Verify user has access to all listings
      if (req.user?.role !== 'super_admin') {
        const listings = await prisma.listing.findMany({
          where: { id: { in: validatedData.listingIds } },
          select: { id: true, ebayAccountId: true },
        });
        
        const unauthorizedListings = listings.filter(
          listing => !req.user?.accountIds.includes(listing.ebayAccountId)
        );
        
        if (unauthorizedListings.length > 0) {
          return res.status(403).json({
            success: false,
            error: `Access denied to listings: ${unauthorizedListings.map(l => l.id).join(', ')}`,
          });
        }
      }
      
      const result = await listingService.bulkUpdateListings(
        validatedData.listingIds,
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

  async getListingSummary(req: Request, res: Response<ApiResponse>) {
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
      
      const summary = await listingService.getListingSummary(accountId, dateRange);
      
      res.json({
        success: true,
        data: summary,
      });
    } catch (error) {
      res.status(500).json({
        success: false,
        error: error instanceof Error ? error.message : 'Failed to get listing summary',
      });
    }
  }

  async getListingPerformance(req: Request, res: Response<ApiResponse>) {
    try {
      const listingId = parseInt(req.params.id);
      
      // Check access
      const listing = await listingService.getListingById(listingId);
      if (req.user?.role !== 'super_admin' && !req.user?.accountIds.includes(listing.account.id)) {
        return res.status(403).json({
          success: false,
          error: 'Access denied to this listing',
        });
      }
      
      const performance = await performanceService.analyzeListingPerformance(listingId);
      
      res.json({
        success: true,
        data: performance,
      });
    } catch (error) {
      res.status(500).json({
        success: false,
        error: error instanceof Error ? error.message : 'Failed to analyze performance',
      });
    }
  }

  async getOptimizationSuggestions(req: Request, res: Response<ApiResponse>) {
    try {
      const listingId = parseInt(req.params.id);
      
      // Check access
      const listing = await listingService.getListingById(listingId);
      if (req.user?.role !== 'super_admin' && !req.user?.accountIds.includes(listing.account.id)) {
        return res.status(403).json({
          success: false,
          error: 'Access denied to this listing',
        });
      }
      
      const suggestions = await performanceService.generateOptimizationSuggestions(listingId);
      
      res.json({
        success: true,
        data: suggestions,
      });
    } catch (error) {
      res.status(500).json({
        success: false,
        error: error instanceof Error ? error.message : 'Failed to generate suggestions',
      });
    }
  }

  async searchListings(req: Request, res: Response<ApiResponse>) {
    try {
      const query = req.query.q as string;
      const limit = parseInt(req.query.limit as string) || 20;
      
      if (!query || query.trim().length < 2) {
        return res.status(400).json({
          success: false,
          error: 'Search query must be at least 2 characters',
        });
      }
      
      const results = await listingService.searchListings(
        query.trim(),
        req.user?.accountIds,
        limit
      );
      
      res.json({
        success: true,
        data: results,
        meta: { count: results.length, query },
      });
    } catch (error) {
      res.status(500).json({
        success: false,
        error: error instanceof Error ? error.message : 'Search failed',
      });
    }
  }

  async exportListings(req: Request, res: Response) {
    try {
      const format = (req.query.format as 'csv' | 'excel') || 'csv';
      
      const filters = listingFilterSchema.parse({
        status: req.query.status ? (req.query.status as string).split(',') : undefined,
        format: req.query.format ? (req.query.format as string).split(',') : undefined,
        categoryName: req.query.categoryName as string,
      });
      
      const result = await listingService.exportListings(
        filters,
        req.user?.accountIds,
        format
      );
      
      // Set headers for file download
      res.setHeader('Content-Type', 'text/csv');
      res.setHeader('Content-Disposition', `attachment; filename="${result.filename}"`);
      
      // Convert data to CSV format
      const headers = Object.keys(result.data[0] || {});
      const csvContent = [
        headers.join(','),
        ...result.data.map(row => 
          headers.map(header => JSON.stringify(row[header] || '')).join(',')
        ),
      ].join('\n');
      
      res.send(csvContent);
    } catch (error) {
      res.status(500).json({
        success: false,
        error: error instanceof Error ? error.message : 'Export failed',
      });
    }
  }
}
```

### 7. Database Schema Updates
```prisma
// Add to existing schema in prisma/schema.prisma

model DraftListing {
  id                   Int      @id @default(autoincrement())
  accountId            Int      @map("account_id")
  title                String   @db.VarChar(255)
  description          String?  @db.Text
  sku                  String?  @db.VarChar(100)
  categoryName         String   @map("category_name") @db.VarChar(100)
  condition            String   @db.VarChar(50)
  startPrice           Decimal  @map("start_price") @db.Decimal(10, 2)
  quantity             Int
  format               String   @db.VarChar(20)
  duration             Int      @default(7) // days
  images               String?  @db.Text // JSON array
  shippingProfile      String?  @map("shipping_profile") @db.Text // JSON
  returnPolicy         String?  @map("return_policy") @db.Text // JSON
  itemSpecifics        String?  @map("item_specifics") @db.Text // JSON
  scheduledStartDate   DateTime? @map("scheduled_start_date")
  status               String   @default("draft") @db.VarChar(20)
  publishedItemNumber  BigInt?  @map("published_item_number")
  publishedAt          DateTime? @map("published_at")
  createdBy            Int      @map("created_by")
  createdAt            DateTime @default(now()) @map("created_at")
  updatedAt            DateTime @updatedAt @map("updated_at")

  // Relations
  account              EbayAccount @relation(fields: [accountId], references: [id], onDelete: Cascade)
  createdByUser        User        @relation(fields: [createdBy], references: [id])

  @@map("draft_listings")
}

model ListingHistory {
  id         Int      @id @default(autoincrement())
  listingId  Int      @map("listing_id")
  changes    String   @db.Text // JSON of changes
  updatedBy  Int      @map("updated_by")
  updatedAt  DateTime @default(now()) @map("updated_at")

  // Relations
  listing    Listing  @relation(fields: [listingId], references: [id], onDelete: Cascade)
  updatedByUser User  @relation(fields: [updatedBy], references: [id])

  @@map("listing_history")
}

// Update existing models to include new relations
model EbayAccount {
  // ... existing fields ...
  
  // Relations
  user               User     @relation(fields: [userId], references: [id], onDelete: Cascade)
  accountPermissions UserAccountPermission[]
  syncHistory        SyncHistory[]
  listings           Listing[]
  orders             Order[]
  draftListings      DraftListing[]

  @@map("ebay_accounts")
}

model User {
  // ... existing fields ...
  
  // Relations
  ebayAccounts        EbayAccount[]
  accountPermissions  UserAccountPermission[]
  assignedPermissions UserAccountPermission[] @relation("AssignedBy")
  orderStatusUpdates  OrderStatusHistory[]
  draftListings       DraftListing[]
  listingHistory      ListingHistory[]

  @@map("users")
}

model Listing {
  // ... existing fields ...
  
  // Relations
  account           EbayAccount   @relation(fields: [ebayAccountId], references: [id], onDelete: Cascade)
  orderItems        OrderItem[]
  listingHistory    ListingHistory[]

  @@unique([itemNumber, ebayAccountId])
  @@map("listings")
}
```

### 8. API Routes
```typescript
// src/routes/listing.routes.ts
import { Router } from 'express';
import { ListingController } from '../controllers/listing.controller';
import { DraftListingController } from '../controllers/draft-listing.controller';
import { authenticate, checkAccountAccess } from '../middleware/auth.middleware';

const router = Router();
const listingController = new ListingController();
const draftController = new DraftListingController();

// All routes require authentication
router.use(authenticate);

// Listing CRUD operations
router.get('/', listingController.getListings.bind(listingController));
router.get('/summary', listingController.getListingSummary.bind(listingController));
router.get('/search', listingController.searchListings.bind(listingController));
router.get('/export', listingController.exportListings.bind(listingController));
router.get('/:id', listingController.getListingById.bind(listingController));
router.put('/:id', listingController.updateListing.bind(listingController));
router.post('/bulk-update', listingController.bulkUpdateListings.bind(listingController));

// Performance and optimization
router.get('/:id/performance', listingController.getListingPerformance.bind(listingController));
router.get('/:id/suggestions', listingController.getOptimizationSuggestions.bind(listingController));

// Draft listings
router.post('/drafts', draftController.createDraft.bind(draftController));
router.get('/drafts', draftController.getDrafts.bind(draftController));
router.get('/drafts/:id', draftController.getDraftById.bind(draftController));
router.put('/drafts/:id', draftController.updateDraft.bind(draftController));
router.delete('/drafts/:id', draftController.deleteDraft.bind(draftController));
router.post('/drafts/:id/duplicate', draftController.duplicateDraft.bind(draftController));

export default router;
```

## Success Criteria

1. ✅ Comprehensive listing management with filtering
2. ✅ Bulk listing operations
3. ✅ Draft listing system with scheduling
4. ✅ Performance analysis and optimization suggestions  
5. ✅ Listing search and export functionality
6. ✅ Category-based organization
7. ✅ Listing history tracking
8. ✅ Ending soon and low stock alerts
9. ✅ Sales performance metrics
10. ✅ Role-based access control for all operations

## Next Steps
- Plan 6: Product & Supplier Management Module
- Plan 7: Customer Management & Communication Module
- Plan 8: Frontend Dashboard Implementation