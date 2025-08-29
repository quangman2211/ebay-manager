# Plan 6: Product & Supplier Management Module

## Objective
Build comprehensive product and supplier management system with inventory tracking, cost analysis, supplier performance monitoring, and automated reordering capabilities.

## Dependencies
- Plan 1: Database Setup & Foundation completed
- Plan 2: Authentication & User Management APIs completed  
- Plan 3: CSV Processing Engine completed
- Plan 4: Order Management Module completed
- Plan 5: Listing Management Module completed

## File Structure Updates
```
src/
├── services/
│   ├── product.service.ts
│   ├── supplier.service.ts
│   ├── inventory.service.ts
│   └── supplier-performance.service.ts
├── controllers/
│   ├── product.controller.ts
│   ├── supplier.controller.ts
│   └── inventory.controller.ts
├── routes/
│   ├── product.routes.ts
│   └── supplier.routes.ts
├── schemas/
│   ├── product.schema.ts
│   └── supplier.schema.ts
├── types/
│   ├── product.types.ts
│   └── supplier.types.ts
├── utils/
│   ├── inventory-calculator.ts
│   └── supplier-analyzer.ts
└── jobs/
    ├── inventory-sync.job.ts
    └── reorder-alert.job.ts
```

## Implementation Files

### 1. Product & Supplier Type Definitions
```typescript
// src/types/product.types.ts

export interface ProductFilter {
  supplierId?: number;
  categoryId?: number;
  sku?: string;
  productName?: string;
  priceRange?: {
    min: number;
    max: number;
  };
  stockLevel?: StockLevel[];
  status?: ProductStatus[];
  profitMargin?: {
    min: number;
    max: number;
  };
  lastOrderDate?: {
    start: Date;
    end: Date;
  };
}

export type ProductStatus = 'active' | 'inactive' | 'discontinued' | 'out_of_stock';
export type StockLevel = 'in_stock' | 'low_stock' | 'out_of_stock' | 'overstock';
export type RestockStatus = 'not_needed' | 'recommended' | 'urgent' | 'ordered' | 'received';

export interface Product {
  id: number;
  sku: string;
  productName: string;
  supplierId: number;
  categoryId?: number;
  description?: string;
  costPrice: number;
  suggestedPrice: number;
  currentMargin: number;
  weight?: number;
  dimensions?: string;
  images?: string[];
  tags?: string[];
  barcode?: string;
  isbn?: string;
  upc?: string;
  ean?: string;
  status: ProductStatus;
  createdAt: Date;
  updatedAt: Date;
}

export interface ProductStock {
  id: number;
  productId: number;
  supplierId: number;
  quantityAvailable: number;
  quantityReserved: number;
  quantityOnOrder: number;
  reorderLevel: number;
  reorderQuantity: number;
  maxStockLevel: number;
  lastRestockDate?: Date;
  nextRestockDate?: Date;
  restockStatus: RestockStatus;
  averageSalesPerMonth: number;
  stockValue: number;
  lastUpdated: Date;
}

export interface Supplier {
  id: number;
  supplierName: string;
  contactName?: string;
  contactEmail?: string;
  contactPhone?: string;
  address?: SupplierAddress;
  website?: string;
  paymentTerms?: string;
  shippingTerms?: string;
  taxId?: string;
  notes?: string;
  rating: number;
  status: SupplierStatus;
  createdAt: Date;
  updatedAt: Date;
}

export interface SupplierAddress {
  street: string;
  city: string;
  state: string;
  zipCode: string;
  country: string;
}

export type SupplierStatus = 'active' | 'inactive' | 'suspended' | 'pending_approval';

export interface SupplierPerformance {
  supplierId: number;
  totalOrders: number;
  totalValue: number;
  averageOrderValue: number;
  onTimeDeliveryRate: number;
  qualityRating: number;
  communicationRating: number;
  priceCompetitiveness: number;
  overallScore: number;
  lastOrderDate?: Date;
  averageLeadTime: number;
  defectRate: number;
  returnRate: number;
  recommendationLevel: 'excellent' | 'good' | 'average' | 'poor';
}

export interface ProductAnalytics {
  productId: number;
  totalSales: number;
  totalRevenue: number;
  totalProfit: number;
  averageSalePrice: number;
  profitMargin: number;
  salesVelocity: number; // units per month
  turnoverRate: number;
  daysInStock: number;
  bestSellingVariants: string[];
  seasonalTrends: Array<{
    month: number;
    sales: number;
    revenue: number;
  }>;
}

export interface RestockRecommendation {
  productId: number;
  currentStock: number;
  reorderLevel: number;
  recommendedQuantity: number;
  urgencyLevel: 'low' | 'medium' | 'high' | 'critical';
  daysUntilStockout: number;
  estimatedCost: number;
  expectedDeliveryDate: Date;
  reasoning: string[];
}

export interface BulkProductUpdate {
  productIds: number[];
  updates: {
    supplierId?: number;
    categoryId?: number;
    costPrice?: number;
    suggestedPrice?: number;
    status?: ProductStatus;
    reorderLevel?: number;
    tags?: string[];
  };
}
```

### 2. Product & Supplier Schemas
```typescript
// src/schemas/product.schema.ts
import { z } from 'zod';

export const createProductSchema = z.object({
  sku: z.string().min(1).max(100),
  productName: z.string().min(1).max(255),
  supplierId: z.number().positive(),
  categoryId: z.number().positive().optional(),
  description: z.string().max(2000).optional(),
  costPrice: z.number().min(0),
  suggestedPrice: z.number().min(0),
  weight: z.number().min(0).optional(),
  dimensions: z.string().max(100).optional(),
  images: z.array(z.string().url()).max(10).optional(),
  tags: z.array(z.string().max(50)).max(20).optional(),
  barcode: z.string().max(50).optional(),
  isbn: z.string().max(20).optional(),
  upc: z.string().max(20).optional(),
  ean: z.string().max(20).optional(),
  status: z.enum(['active', 'inactive', 'discontinued', 'out_of_stock']).default('active'),
});

export const updateProductSchema = createProductSchema.partial();

export const createProductStockSchema = z.object({
  productId: z.number().positive(),
  supplierId: z.number().positive(),
  quantityAvailable: z.number().min(0),
  quantityReserved: z.number().min(0).default(0),
  quantityOnOrder: z.number().min(0).default(0),
  reorderLevel: z.number().min(0).default(10),
  reorderQuantity: z.number().min(1).default(50),
  maxStockLevel: z.number().min(1).default(200),
});

export const updateProductStockSchema = createProductStockSchema.partial().omit(['productId', 'supplierId']);

export const createSupplierSchema = z.object({
  supplierName: z.string().min(1).max(255),
  contactName: z.string().max(255).optional(),
  contactEmail: z.string().email().max(255).optional(),
  contactPhone: z.string().max(50).optional(),
  address: z.object({
    street: z.string().max(255),
    city: z.string().max(100),
    state: z.string().max(100),
    zipCode: z.string().max(20),
    country: z.string().max(100),
  }).optional(),
  website: z.string().url().max(255).optional(),
  paymentTerms: z.string().max(255).optional(),
  shippingTerms: z.string().max(255).optional(),
  taxId: z.string().max(50).optional(),
  notes: z.string().max(2000).optional(),
  rating: z.number().min(1).max(5).default(3),
  status: z.enum(['active', 'inactive', 'suspended', 'pending_approval']).default('active'),
});

export const updateSupplierSchema = createSupplierSchema.partial();

export const productFilterSchema = z.object({
  supplierId: z.number().positive().optional(),
  categoryId: z.number().positive().optional(),
  sku: z.string().max(100).optional(),
  productName: z.string().max(255).optional(),
  priceRange: z.object({
    min: z.number().min(0),
    max: z.number().min(0),
  }).optional(),
  stockLevel: z.array(z.enum(['in_stock', 'low_stock', 'out_of_stock', 'overstock'])).optional(),
  status: z.array(z.enum(['active', 'inactive', 'discontinued', 'out_of_stock'])).optional(),
  profitMargin: z.object({
    min: z.number(),
    max: z.number(),
  }).optional(),
});

export const bulkProductUpdateSchema = z.object({
  productIds: z.array(z.number().positive()).min(1).max(100),
  updates: z.object({
    supplierId: z.number().positive().optional(),
    categoryId: z.number().positive().optional(),
    costPrice: z.number().min(0).optional(),
    suggestedPrice: z.number().min(0).optional(),
    status: z.enum(['active', 'inactive', 'discontinued', 'out_of_stock']).optional(),
    reorderLevel: z.number().min(0).optional(),
    tags: z.array(z.string().max(50)).max(20).optional(),
  }),
});

export const importProductsSchema = z.object({
  supplierId: z.number().positive(),
  replaceExisting: z.boolean().default(false),
  updatePricesOnly: z.boolean().default(false),
  dryRun: z.boolean().default(false),
});

export type CreateProductInput = z.infer<typeof createProductSchema>;
export type UpdateProductInput = z.infer<typeof updateProductSchema>;
export type CreateProductStockInput = z.infer<typeof createProductStockSchema>;
export type UpdateProductStockInput = z.infer<typeof updateProductStockSchema>;
export type CreateSupplierInput = z.infer<typeof createSupplierSchema>;
export type UpdateSupplierInput = z.infer<typeof updateSupplierSchema>;
export type ProductFilterInput = z.infer<typeof productFilterSchema>;
export type BulkProductUpdateInput = z.infer<typeof bulkProductUpdateSchema>;
export type ImportProductsInput = z.infer<typeof importProductsSchema>;
```

### 3. Supplier Service
```typescript
// src/services/supplier.service.ts
import { prisma } from '../config/database';
import { CreateSupplierInput, UpdateSupplierInput } from '../schemas/product.schema';
import { PaginationParams, FilterParams } from '../types/common.types';
import { SupplierPerformance } from '../types/product.types';

export class SupplierService {
  async createSupplier(data: CreateSupplierInput, createdBy: number) {
    const supplier = await prisma.supplier.create({
      data: {
        supplierName: data.supplierName,
        contactName: data.contactName,
        contactEmail: data.contactEmail,
        contactPhone: data.contactPhone,
        address: data.address ? JSON.stringify(data.address) : null,
        website: data.website,
        paymentTerms: data.paymentTerms,
        shippingTerms: data.shippingTerms,
        taxId: data.taxId,
        notes: data.notes,
        rating: data.rating || 3,
        status: data.status || 'active',
        createdBy,
      },
    });

    return {
      ...supplier,
      address: supplier.address ? JSON.parse(supplier.address) : null,
    };
  }

  async getSuppliers(
    pagination: PaginationParams,
    filters: FilterParams & { status?: string; minRating?: number }
  ) {
    const { page = 1, limit = 20, sortBy = 'supplierName', sortOrder = 'asc' } = pagination;
    const { search, status, minRating } = filters;
    
    const skip = (page - 1) * limit;
    const where: any = {};

    if (search) {
      where.OR = [
        { supplierName: { contains: search, mode: 'insensitive' } },
        { contactName: { contains: search, mode: 'insensitive' } },
        { contactEmail: { contains: search, mode: 'insensitive' } },
      ];
    }

    if (status) {
      where.status = status;
    }

    if (minRating !== undefined) {
      where.rating = { gte: minRating };
    }

    const [suppliers, total] = await Promise.all([
      prisma.supplier.findMany({
        where,
        skip,
        take: limit,
        orderBy: { [sortBy]: sortOrder },
        include: {
          _count: {
            select: {
              products: true,
              productStock: true,
            },
          },
        },
      }),
      prisma.supplier.count({ where }),
    ]);

    return {
      suppliers: suppliers.map(supplier => ({
        ...supplier,
        address: supplier.address ? JSON.parse(supplier.address) : null,
        productCount: supplier._count.products,
        stockRecordCount: supplier._count.productStock,
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

  async getSupplierById(supplierId: number) {
    const supplier = await prisma.supplier.findUnique({
      where: { id: supplierId },
      include: {
        products: {
          select: {
            id: true,
            sku: true,
            productName: true,
            costPrice: true,
            suggestedPrice: true,
            status: true,
            stock: {
              select: {
                quantityAvailable: true,
                reorderLevel: true,
                restockStatus: true,
              },
            },
          },
          orderBy: { productName: 'asc' },
        },
        createdByUser: {
          select: {
            username: true,
            fullName: true,
          },
        },
      },
    });

    if (!supplier) {
      throw new Error('Supplier not found');
    }

    // Calculate supplier statistics
    const totalProducts = supplier.products.length;
    const activeProducts = supplier.products.filter(p => p.status === 'active').length;
    const totalValue = supplier.products.reduce((sum, product) => 
      sum + (Number(product.costPrice) * (product.stock?.[0]?.quantityAvailable || 0)), 0
    );
    const lowStockProducts = supplier.products.filter(p => 
      p.stock?.[0] && p.stock[0].quantityAvailable <= p.stock[0].reorderLevel
    ).length;

    return {
      ...supplier,
      address: supplier.address ? JSON.parse(supplier.address) : null,
      statistics: {
        totalProducts,
        activeProducts,
        totalValue,
        lowStockProducts,
        averageProductPrice: totalProducts > 0 ? 
          supplier.products.reduce((sum, p) => sum + Number(p.costPrice), 0) / totalProducts : 0,
      },
    };
  }

  async updateSupplier(supplierId: number, data: UpdateSupplierInput) {
    const updateData: any = { ...data };
    
    if (data.address) {
      updateData.address = JSON.stringify(data.address);
    }

    const updatedSupplier = await prisma.supplier.update({
      where: { id: supplierId },
      data: updateData,
    });

    return {
      ...updatedSupplier,
      address: updatedSupplier.address ? JSON.parse(updatedSupplier.address) : null,
    };
  }

  async getSupplierPerformance(supplierId: number, dateRange?: { start: Date; end: Date }): Promise<SupplierPerformance> {
    const where: any = { supplierId };
    
    if (dateRange) {
      where.createdAt = {
        gte: dateRange.start,
        lte: dateRange.end,
      };
    }

    // Get purchase orders and related data for this supplier
    const [
      purchaseOrders,
      products,
      supplier,
    ] = await Promise.all([
      prisma.purchaseOrder.findMany({
        where,
        include: {
          items: true,
        },
      }),
      prisma.product.findMany({
        where: { supplierId },
        include: {
          stock: true,
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
      }),
      prisma.supplier.findUnique({
        where: { id: supplierId },
        select: { rating: true },
      }),
    ]);

    // Calculate performance metrics
    const totalOrders = purchaseOrders.length;
    const totalValue = purchaseOrders.reduce((sum, order) => sum + Number(order.totalAmount), 0);
    const averageOrderValue = totalOrders > 0 ? totalValue / totalOrders : 0;

    // Calculate on-time delivery rate (simplified - would need actual delivery tracking)
    const onTimeDeliveryRate = purchaseOrders.length > 0 ? 
      purchaseOrders.filter(order => order.status === 'completed').length / totalOrders * 100 : 0;

    // Calculate quality metrics from product returns/issues
    const totalProductsSold = products.reduce((sum, product) => 
      sum + product.orderItems.reduce((itemSum, item) => itemSum + item.quantity, 0), 0
    );
    
    const defectRate = 0; // Would calculate from return data
    const returnRate = 0; // Would calculate from return data

    // Calculate average lead time (simplified)
    const averageLeadTime = purchaseOrders.length > 0 ?
      purchaseOrders.reduce((sum, order) => {
        if (order.deliveredAt && order.createdAt) {
          return sum + Math.floor((order.deliveredAt.getTime() - order.createdAt.getTime()) / (1000 * 60 * 60 * 24));
        }
        return sum + 7; // Default 7 days if no data
      }, 0) / totalOrders : 7;

    const lastOrderDate = purchaseOrders.length > 0 ?
      purchaseOrders.sort((a, b) => b.createdAt.getTime() - a.createdAt.getTime())[0].createdAt : undefined;

    // Calculate overall score
    const qualityRating = supplier?.rating || 3;
    const communicationRating = qualityRating; // Simplified
    const priceCompetitiveness = 3; // Would need market data

    const overallScore = (
      (onTimeDeliveryRate / 100) * 30 +
      (qualityRating / 5) * 25 +
      (communicationRating / 5) * 20 +
      (priceCompetitiveness / 5) * 15 +
      (Math.min(averageOrderValue / 1000, 1)) * 10
    ) * 100;

    let recommendationLevel: 'excellent' | 'good' | 'average' | 'poor';
    if (overallScore >= 80) recommendationLevel = 'excellent';
    else if (overallScore >= 60) recommendationLevel = 'good';
    else if (overallScore >= 40) recommendationLevel = 'average';
    else recommendationLevel = 'poor';

    return {
      supplierId,
      totalOrders,
      totalValue,
      averageOrderValue,
      onTimeDeliveryRate,
      qualityRating,
      communicationRating,
      priceCompetitiveness,
      overallScore: Math.round(overallScore),
      lastOrderDate,
      averageLeadTime,
      defectRate,
      returnRate,
      recommendationLevel,
    };
  }

  async getSupplierComparison(supplierIds: number[], metrics: string[] = ['price', 'quality', 'delivery']) {
    const suppliers = await Promise.all(
      supplierIds.map(id => this.getSupplierPerformance(id))
    );

    const comparison = suppliers.map(supplier => ({
      supplierId: supplier.supplierId,
      metrics: {
        price: supplier.priceCompetitiveness,
        quality: supplier.qualityRating,
        delivery: supplier.onTimeDeliveryRate,
        communication: supplier.communicationRating,
        overall: supplier.overallScore,
      },
      recommendationLevel: supplier.recommendationLevel,
    }));

    return {
      suppliers: comparison,
      bestPerformer: comparison.reduce((best, current) => 
        current.metrics.overall > best.metrics.overall ? current : best
      ),
      averageScores: {
        price: comparison.reduce((sum, s) => sum + s.metrics.price, 0) / comparison.length,
        quality: comparison.reduce((sum, s) => sum + s.metrics.quality, 0) / comparison.length,
        delivery: comparison.reduce((sum, s) => sum + s.metrics.delivery, 0) / comparison.length,
        overall: comparison.reduce((sum, s) => sum + s.metrics.overall, 0) / comparison.length,
      },
    };
  }

  async toggleSupplierStatus(supplierId: number) {
    const supplier = await prisma.supplier.findUnique({
      where: { id: supplierId },
      select: { status: true, supplierName: true },
    });

    if (!supplier) {
      throw new Error('Supplier not found');
    }

    const newStatus = supplier.status === 'active' ? 'inactive' : 'active';
    
    const updatedSupplier = await prisma.supplier.update({
      where: { id: supplierId },
      data: { status: newStatus },
    });

    return {
      ...updatedSupplier,
      address: updatedSupplier.address ? JSON.parse(updatedSupplier.address) : null,
    };
  }

  async deleteSupplier(supplierId: number) {
    // Check if supplier has products
    const productCount = await prisma.product.count({
      where: { supplierId },
    });

    if (productCount > 0) {
      throw new Error('Cannot delete supplier with existing products. Transfer products to another supplier first.');
    }

    await prisma.supplier.delete({
      where: { id: supplierId },
    });

    return { success: true };
  }

  async getSupplierStatistics() {
    const [
      totalSuppliers,
      activeSuppliers,
      statusBreakdown,
      ratingDistribution,
      topSuppliers,
    ] = await Promise.all([
      prisma.supplier.count(),
      prisma.supplier.count({ where: { status: 'active' } }),
      prisma.supplier.groupBy({
        by: ['status'],
        _count: { id: true },
      }),
      prisma.supplier.groupBy({
        by: ['rating'],
        _count: { id: true },
      }),
      prisma.supplier.findMany({
        include: {
          _count: {
            select: { products: true },
          },
        },
        orderBy: {
          products: { _count: 'desc' },
        },
        take: 5,
      }),
    ]);

    return {
      totalSuppliers,
      activeSuppliers,
      inactiveSuppliers: totalSuppliers - activeSuppliers,
      statusBreakdown: statusBreakdown.reduce((acc, item) => ({
        ...acc,
        [item.status]: item._count.id,
      }), {}),
      ratingDistribution: ratingDistribution.reduce((acc, item) => ({
        ...acc,
        [item.rating]: item._count.id,
      }), {}),
      topSuppliers: topSuppliers.map(supplier => ({
        ...supplier,
        address: supplier.address ? JSON.parse(supplier.address) : null,
        productCount: supplier._count.products,
        _count: undefined,
      })),
    };
  }
}
```

### 4. Product Service
```typescript
// src/services/product.service.ts
import { prisma } from '../config/database';
import { CreateProductInput, UpdateProductInput, ProductFilterInput } from '../schemas/product.schema';
import { PaginationParams } from '../types/common.types';
import { ProductAnalytics, RestockRecommendation } from '../types/product.types';

export class ProductService {
  async createProduct(data: CreateProductInput, createdBy: number) {
    // Check if SKU already exists
    const existingProduct = await prisma.product.findFirst({
      where: { sku: data.sku },
    });

    if (existingProduct) {
      throw new Error('Product with this SKU already exists');
    }

    const product = await prisma.product.create({
      data: {
        sku: data.sku,
        productName: data.productName,
        supplierId: data.supplierId,
        categoryId: data.categoryId,
        description: data.description,
        costPrice: data.costPrice,
        suggestedPrice: data.suggestedPrice,
        weight: data.weight,
        dimensions: data.dimensions,
        images: data.images ? JSON.stringify(data.images) : null,
        tags: data.tags ? JSON.stringify(data.tags) : null,
        barcode: data.barcode,
        isbn: data.isbn,
        upc: data.upc,
        ean: data.ean,
        status: data.status || 'active',
        createdBy,
      },
      include: {
        supplier: {
          select: {
            supplierName: true,
          },
        },
        category: {
          select: {
            name: true,
          },
        },
      },
    });

    return {
      ...product,
      images: product.images ? JSON.parse(product.images) : [],
      tags: product.tags ? JSON.parse(product.tags) : [],
      currentMargin: this.calculateMargin(Number(product.costPrice), Number(product.suggestedPrice)),
    };
  }

  async getProducts(
    pagination: PaginationParams,
    filters: ProductFilterInput
  ) {
    const { page = 1, limit = 20, sortBy = 'productName', sortOrder = 'asc' } = pagination;
    const skip = (page - 1) * limit;
    
    const where: any = {};
    
    if (filters.supplierId) {
      where.supplierId = filters.supplierId;
    }
    
    if (filters.categoryId) {
      where.categoryId = filters.categoryId;
    }
    
    if (filters.sku) {
      where.sku = {
        contains: filters.sku,
        mode: 'insensitive',
      };
    }
    
    if (filters.productName) {
      where.productName = {
        contains: filters.productName,
        mode: 'insensitive',
      };
    }
    
    if (filters.priceRange) {
      where.costPrice = {
        gte: filters.priceRange.min,
        lte: filters.priceRange.max,
      };
    }
    
    if (filters.status && filters.status.length > 0) {
      where.status = { in: filters.status };
    }

    const [products, total] = await Promise.all([
      prisma.product.findMany({
        where,
        skip,
        take: limit,
        orderBy: { [sortBy]: sortOrder },
        include: {
          supplier: {
            select: {
              id: true,
              supplierName: true,
              status: true,
            },
          },
          category: {
            select: {
              id: true,
              name: true,
            },
          },
          stock: {
            select: {
              quantityAvailable: true,
              quantityReserved: true,
              reorderLevel: true,
              restockStatus: true,
              lastUpdated: true,
            },
          },
          _count: {
            select: {
              listings: true,
              orderItems: true,
            },
          },
        },
      }),
      prisma.product.count({ where }),
    ]);

    return {
      products: products.map(product => {
        const stock = product.stock?.[0];
        const stockLevel = this.determineStockLevel(
          stock?.quantityAvailable || 0,
          stock?.reorderLevel || 0
        );
        
        return {
          ...product,
          images: product.images ? JSON.parse(product.images) : [],
          tags: product.tags ? JSON.parse(product.tags) : [],
          currentMargin: this.calculateMargin(Number(product.costPrice), Number(product.suggestedPrice)),
          stockLevel,
          currentStock: stock?.quantityAvailable || 0,
          reservedStock: stock?.quantityReserved || 0,
          reorderLevel: stock?.reorderLevel || 0,
          restockStatus: stock?.restockStatus || 'not_needed',
          listingsCount: product._count.listings,
          salesCount: product._count.orderItems,
          stock: undefined,
          _count: undefined,
        };
      }),
      pagination: {
        page,
        limit,
        total,
        totalPages: Math.ceil(total / limit),
      },
    };
  }

  async getProductById(productId: number) {
    const product = await prisma.product.findUnique({
      where: { id: productId },
      include: {
        supplier: {
          select: {
            id: true,
            supplierName: true,
            contactEmail: true,
            status: true,
          },
        },
        category: {
          select: {
            id: true,
            name: true,
          },
        },
        stock: true,
        listings: {
          select: {
            id: true,
            itemNumber: true,
            title: true,
            currentPrice: true,
            availableQuantity: true,
            soldQuantity: true,
            listingStatus: true,
            watchers: true,
            account: {
              select: {
                accountName: true,
              },
            },
          },
        },
        orderItems: {
          include: {
            order: {
              select: {
                orderDate: true,
                buyerUsername: true,
                totalAmount: true,
                paymentStatus: true,
              },
            },
          },
          orderBy: {
            order: { orderDate: 'desc' },
          },
          take: 10,
        },
        createdByUser: {
          select: {
            username: true,
            fullName: true,
          },
        },
      },
    });

    if (!product) {
      throw new Error('Product not found');
    }

    // Calculate analytics
    const totalSales = product.orderItems.reduce((sum, item) => sum + item.quantity, 0);
    const totalRevenue = product.orderItems.reduce((sum, item) => 
      sum + (Number(item.unitPrice) * item.quantity), 0
    );
    const averageSalePrice = totalSales > 0 ? totalRevenue / totalSales : Number(product.suggestedPrice);
    const totalProfit = product.orderItems.reduce((sum, item) => {
      const profit = (Number(item.unitPrice) - Number(product.costPrice)) * item.quantity;
      return sum + profit;
    }, 0);

    return {
      ...product,
      images: product.images ? JSON.parse(product.images) : [],
      tags: product.tags ? JSON.parse(product.tags) : [],
      currentMargin: this.calculateMargin(Number(product.costPrice), Number(product.suggestedPrice)),
      analytics: {
        totalSales,
        totalRevenue,
        totalProfit,
        averageSalePrice,
        profitMargin: totalRevenue > 0 ? (totalProfit / totalRevenue) * 100 : 0,
        salesVelocity: this.calculateSalesVelocity(product.orderItems),
      },
      salesHistory: product.orderItems.map(item => ({
        date: item.order.orderDate,
        buyer: item.order.buyerUsername,
        quantity: item.quantity,
        price: Number(item.unitPrice),
        total: Number(item.totalPrice),
        status: item.order.paymentStatus,
      })),
    };
  }

  async updateProduct(productId: number, data: UpdateProductInput) {
    const updateData: any = { ...data };
    
    if (data.images) {
      updateData.images = JSON.stringify(data.images);
    }
    
    if (data.tags) {
      updateData.tags = JSON.stringify(data.tags);
    }

    const updatedProduct = await prisma.product.update({
      where: { id: productId },
      data: updateData,
      include: {
        supplier: {
          select: {
            supplierName: true,
          },
        },
        stock: {
          select: {
            quantityAvailable: true,
            reorderLevel: true,
          },
        },
      },
    });

    return {
      ...updatedProduct,
      images: updatedProduct.images ? JSON.parse(updatedProduct.images) : [],
      tags: updatedProduct.tags ? JSON.parse(updatedProduct.tags) : [],
      currentMargin: this.calculateMargin(Number(updatedProduct.costPrice), Number(updatedProduct.suggestedPrice)),
    };
  }

  async bulkUpdateProducts(
    productIds: number[],
    updates: any,
    updatedBy: number
  ) {
    const results = {
      updated: 0,
      failed: 0,
      errors: [] as string[],
    };

    // Process in batches
    const batchSize = 20;
    for (let i = 0; i < productIds.length; i += batchSize) {
      const batch = productIds.slice(i, i + batchSize);
      
      const promises = batch.map(async (productId) => {
        try {
          await this.updateProduct(productId, updates);
          results.updated++;
        } catch (error) {
          results.failed++;
          results.errors.push(`Product ${productId}: ${error instanceof Error ? error.message : 'Unknown error'}`);
        }
      });

      await Promise.all(promises);
    }

    return results;
  }

  async getProductAnalytics(
    productId: number,
    dateRange?: { start: Date; end: Date }
  ): Promise<ProductAnalytics> {
    const where: any = { productId };
    
    if (dateRange) {
      where.order = {
        orderDate: {
          gte: dateRange.start,
          lte: dateRange.end,
        },
      };
    }

    const [product, orderItems] = await Promise.all([
      prisma.product.findUnique({
        where: { id: productId },
        select: {
          costPrice: true,
          suggestedPrice: true,
          createdAt: true,
        },
      }),
      prisma.orderItem.findMany({
        where,
        include: {
          order: {
            select: {
              orderDate: true,
              paymentStatus: true,
            },
          },
        },
      }),
    ]);

    if (!product) {
      throw new Error('Product not found');
    }

    const paidItems = orderItems.filter(item => item.order.paymentStatus === 'paid');
    
    const totalSales = paidItems.reduce((sum, item) => sum + item.quantity, 0);
    const totalRevenue = paidItems.reduce((sum, item) => 
      sum + (Number(item.unitPrice) * item.quantity), 0
    );
    const totalProfit = paidItems.reduce((sum, item) => {
      const profit = (Number(item.unitPrice) - Number(product.costPrice)) * item.quantity;
      return sum + profit;
    }, 0);

    const averageSalePrice = totalSales > 0 ? totalRevenue / totalSales : 0;
    const profitMargin = totalRevenue > 0 ? (totalProfit / totalRevenue) * 100 : 0;
    
    // Calculate sales velocity (units per month)
    const daysInStock = Math.max(1, Math.floor(
      (new Date().getTime() - product.createdAt.getTime()) / (1000 * 60 * 60 * 24)
    ));
    const salesVelocity = (totalSales / daysInStock) * 30;

    // Calculate turnover rate (simplified)
    const averageStock = 50; // Would need historical stock data
    const turnoverRate = averageStock > 0 ? totalSales / averageStock : 0;

    // Group sales by month for seasonal trends
    const salesByMonth = paidItems.reduce((acc, item) => {
      const month = item.order.orderDate.getMonth() + 1;
      if (!acc[month]) {
        acc[month] = { sales: 0, revenue: 0 };
      }
      acc[month].sales += item.quantity;
      acc[month].revenue += Number(item.unitPrice) * item.quantity;
      return acc;
    }, {} as { [month: number]: { sales: number; revenue: number } });

    const seasonalTrends = Object.entries(salesByMonth).map(([month, data]) => ({
      month: parseInt(month),
      sales: data.sales,
      revenue: data.revenue,
    }));

    return {
      productId,
      totalSales,
      totalRevenue,
      totalProfit,
      averageSalePrice,
      profitMargin,
      salesVelocity,
      turnoverRate,
      daysInStock,
      bestSellingVariants: [], // Would need variant analysis
      seasonalTrends,
    };
  }

  async getRestockRecommendations(supplierId?: number): Promise<RestockRecommendation[]> {
    const where: any = {};
    if (supplierId) {
      where.supplierId = supplierId;
    }

    const products = await prisma.product.findMany({
      where: {
        ...where,
        status: 'active',
      },
      include: {
        supplier: {
          select: {
            supplierName: true,
            paymentTerms: true,
          },
        },
        stock: true,
        orderItems: {
          where: {
            order: {
              orderDate: {
                gte: new Date(Date.now() - 90 * 24 * 60 * 60 * 1000), // Last 90 days
              },
              paymentStatus: 'paid',
            },
          },
        },
      },
    });

    const recommendations: RestockRecommendation[] = [];

    for (const product of products) {
      const stock = product.stock?.[0];
      if (!stock) continue;

      const currentStock = stock.quantityAvailable;
      const reorderLevel = stock.reorderLevel;
      
      if (currentStock <= reorderLevel) {
        // Calculate sales velocity
        const salesLast90Days = product.orderItems.reduce((sum, item) => sum + item.quantity, 0);
        const salesPerDay = salesLast90Days / 90;
        
        // Days until stockout
        const daysUntilStockout = salesPerDay > 0 ? Math.floor(currentStock / salesPerDay) : 999;
        
        // Recommended quantity based on sales velocity and lead time
        const estimatedLeadTime = 14; // Default 14 days
        const safetyStock = Math.ceil(salesPerDay * 7); // 7 days safety stock
        const leadTimeStock = Math.ceil(salesPerDay * estimatedLeadTime);
        const recommendedQuantity = Math.max(
          stock.reorderQuantity,
          leadTimeStock + safetyStock - currentStock
        );

        // Determine urgency
        let urgencyLevel: 'low' | 'medium' | 'high' | 'critical';
        if (daysUntilStockout <= 3) urgencyLevel = 'critical';
        else if (daysUntilStockout <= 7) urgencyLevel = 'high';
        else if (daysUntilStockout <= 14) urgencyLevel = 'medium';
        else urgencyLevel = 'low';

        const estimatedCost = recommendedQuantity * Number(product.costPrice);
        const expectedDeliveryDate = new Date(Date.now() + estimatedLeadTime * 24 * 60 * 60 * 1000);

        const reasoning = [];
        if (currentStock <= reorderLevel) {
          reasoning.push(`Current stock (${currentStock}) is at or below reorder level (${reorderLevel})`);
        }
        if (salesPerDay > 0) {
          reasoning.push(`Average sales: ${salesPerDay.toFixed(1)} units per day`);
        }
        if (daysUntilStockout <= 14) {
          reasoning.push(`Estimated ${daysUntilStockout} days until stockout`);
        }

        recommendations.push({
          productId: product.id,
          currentStock,
          reorderLevel,
          recommendedQuantity,
          urgencyLevel,
          daysUntilStockout,
          estimatedCost,
          expectedDeliveryDate,
          reasoning,
        });
      }
    }

    return recommendations.sort((a, b) => {
      const urgencyOrder = { critical: 4, high: 3, medium: 2, low: 1 };
      return urgencyOrder[b.urgencyLevel] - urgencyOrder[a.urgencyLevel];
    });
  }

  async searchProducts(query: string, limit: number = 20) {
    const products = await prisma.product.findMany({
      where: {
        OR: [
          { sku: { contains: query, mode: 'insensitive' } },
          { productName: { contains: query, mode: 'insensitive' } },
          { barcode: { equals: query } },
          { isbn: { equals: query } },
          { upc: { equals: query } },
          { ean: { equals: query } },
        ],
      },
      select: {
        id: true,
        sku: true,
        productName: true,
        costPrice: true,
        suggestedPrice: true,
        status: true,
        supplier: {
          select: {
            supplierName: true,
          },
        },
        stock: {
          select: {
            quantityAvailable: true,
          },
        },
      },
      take: limit,
      orderBy: [
        { status: 'asc' }, // Active products first
        { productName: 'asc' },
      ],
    });

    return products.map(product => ({
      ...product,
      currentStock: product.stock?.[0]?.quantityAvailable || 0,
      currentMargin: this.calculateMargin(Number(product.costPrice), Number(product.suggestedPrice)),
      stock: undefined,
    }));
  }

  private calculateMargin(costPrice: number, sellingPrice: number): number {
    if (sellingPrice === 0) return 0;
    return ((sellingPrice - costPrice) / sellingPrice) * 100;
  }

  private determineStockLevel(currentStock: number, reorderLevel: number) {
    if (currentStock === 0) return 'out_of_stock';
    if (currentStock <= reorderLevel) return 'low_stock';
    if (currentStock >= reorderLevel * 5) return 'overstock';
    return 'in_stock';
  }

  private calculateSalesVelocity(orderItems: any[]): number {
    if (orderItems.length === 0) return 0;
    
    const last30Days = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000);
    const recentSales = orderItems.filter(item => 
      item.order.orderDate >= last30Days && item.order.paymentStatus === 'paid'
    );
    
    return recentSales.reduce((sum, item) => sum + item.quantity, 0);
  }
}
```

### 5. Inventory Service
```typescript
// src/services/inventory.service.ts
import { prisma } from '../config/database';
import { CreateProductStockInput, UpdateProductStockInput } from '../schemas/product.schema';

export class InventoryService {
  async createProductStock(data: CreateProductStockInput, createdBy: number) {
    // Check if stock record already exists
    const existingStock = await prisma.productStock.findFirst({
      where: {
        productId: data.productId,
        supplierId: data.supplierId,
      },
    });

    if (existingStock) {
      throw new Error('Stock record already exists for this product-supplier combination');
    }

    const stockRecord = await prisma.productStock.create({
      data: {
        productId: data.productId,
        supplierId: data.supplierId,
        quantityAvailable: data.quantityAvailable,
        quantityReserved: data.quantityReserved || 0,
        quantityOnOrder: data.quantityOnOrder || 0,
        reorderLevel: data.reorderLevel || 10,
        reorderQuantity: data.reorderQuantity || 50,
        maxStockLevel: data.maxStockLevel || 200,
        restockStatus: 'not_needed',
        averageSalesPerMonth: 0,
        stockValue: data.quantityAvailable * 0, // Will be calculated with product cost
      },
    });

    return stockRecord;
  }

  async updateProductStock(productId: number, supplierId: number, data: UpdateProductStockInput) {
    const stockRecord = await prisma.productStock.findFirst({
      where: { productId, supplierId },
    });

    if (!stockRecord) {
      throw new Error('Stock record not found');
    }

    // Calculate new stock value if quantity changed
    let updateData = { ...data };
    if (data.quantityAvailable !== undefined) {
      const product = await prisma.product.findUnique({
        where: { id: productId },
        select: { costPrice: true },
      });
      
      if (product) {
        updateData.stockValue = data.quantityAvailable * Number(product.costPrice);
      }
    }

    const updatedStock = await prisma.productStock.update({
      where: { id: stockRecord.id },
      data: {
        ...updateData,
        lastUpdated: new Date(),
      },
    });

    // Update restock status based on new levels
    const restockStatus = this.calculateRestockStatus(
      updatedStock.quantityAvailable,
      updatedStock.reorderLevel,
      updatedStock.quantityOnOrder
    );

    if (restockStatus !== updatedStock.restockStatus) {
      await prisma.productStock.update({
        where: { id: updatedStock.id },
        data: { restockStatus },
      });
    }

    return updatedStock;
  }

  async adjustStock(
    productId: number,
    supplierId: number,
    adjustment: number,
    reason: string,
    adjustedBy: number
  ) {
    const stockRecord = await prisma.productStock.findFirst({
      where: { productId, supplierId },
      include: {
        product: {
          select: {
            productName: true,
            costPrice: true,
          },
        },
      },
    });

    if (!stockRecord) {
      throw new Error('Stock record not found');
    }

    const newQuantity = Math.max(0, stockRecord.quantityAvailable + adjustment);
    const newStockValue = newQuantity * Number(stockRecord.product.costPrice);

    // Update stock quantity
    const updatedStock = await prisma.productStock.update({
      where: { id: stockRecord.id },
      data: {
        quantityAvailable: newQuantity,
        stockValue: newStockValue,
        lastUpdated: new Date(),
      },
    });

    // Create stock adjustment record
    await prisma.stockAdjustment.create({
      data: {
        productStockId: stockRecord.id,
        adjustmentQuantity: adjustment,
        previousQuantity: stockRecord.quantityAvailable,
        newQuantity,
        reason,
        adjustedBy,
      },
    });

    return updatedStock;
  }

  async reserveStock(productId: number, supplierId: number, quantity: number, reservedBy: number) {
    const stockRecord = await prisma.productStock.findFirst({
      where: { productId, supplierId },
    });

    if (!stockRecord) {
      throw new Error('Stock record not found');
    }

    if (stockRecord.quantityAvailable < quantity) {
      throw new Error('Insufficient stock available for reservation');
    }

    const updatedStock = await prisma.productStock.update({
      where: { id: stockRecord.id },
      data: {
        quantityAvailable: stockRecord.quantityAvailable - quantity,
        quantityReserved: stockRecord.quantityReserved + quantity,
        lastUpdated: new Date(),
      },
    });

    // Create reservation record
    await prisma.stockReservation.create({
      data: {
        productStockId: stockRecord.id,
        reservedQuantity: quantity,
        reservedBy,
        expiresAt: new Date(Date.now() + 24 * 60 * 60 * 1000), // 24 hours
      },
    });

    return updatedStock;
  }

  async releaseReservation(reservationId: number) {
    const reservation = await prisma.stockReservation.findUnique({
      where: { id: reservationId },
      include: {
        productStock: true,
      },
    });

    if (!reservation) {
      throw new Error('Reservation not found');
    }

    if (reservation.status === 'released') {
      throw new Error('Reservation already released');
    }

    // Update stock quantities
    const updatedStock = await prisma.productStock.update({
      where: { id: reservation.productStockId },
      data: {
        quantityAvailable: reservation.productStock.quantityAvailable + reservation.reservedQuantity,
        quantityReserved: reservation.productStock.quantityReserved - reservation.reservedQuantity,
        lastUpdated: new Date(),
      },
    });

    // Mark reservation as released
    await prisma.stockReservation.update({
      where: { id: reservationId },
      data: { 
        status: 'released',
        releasedAt: new Date(),
      },
    });

    return updatedStock;
  }

  async getInventoryReport(supplierId?: number, lowStockOnly: boolean = false) {
    const where: any = {};
    
    if (supplierId) {
      where.supplierId = supplierId;
    }

    if (lowStockOnly) {
      where.AND = [
        { quantityAvailable: { lte: prisma.productStock.fields.reorderLevel } }
      ];
    }

    const inventoryItems = await prisma.productStock.findMany({
      where,
      include: {
        product: {
          select: {
            sku: true,
            productName: true,
            costPrice: true,
            status: true,
          },
        },
        supplier: {
          select: {
            supplierName: true,
          },
        },
      },
      orderBy: [
        { restockStatus: 'desc' },
        { quantityAvailable: 'asc' },
      ],
    });

    return inventoryItems.map(item => ({
      ...item,
      stockLevel: this.determineStockLevel(item.quantityAvailable, item.reorderLevel),
      daysOfStock: this.calculateDaysOfStock(item.quantityAvailable, item.averageSalesPerMonth),
      reorderRecommended: item.quantityAvailable <= item.reorderLevel,
    }));
  }

  async getStockMovements(
    productId?: number,
    supplierId?: number,
    dateRange?: { start: Date; end: Date }
  ) {
    const where: any = {};
    
    if (productId || supplierId) {
      where.productStock = {};
      if (productId) where.productStock.productId = productId;
      if (supplierId) where.productStock.supplierId = supplierId;
    }
    
    if (dateRange) {
      where.createdAt = {
        gte: dateRange.start,
        lte: dateRange.end,
      };
    }

    const movements = await prisma.stockAdjustment.findMany({
      where,
      include: {
        productStock: {
          include: {
            product: {
              select: {
                sku: true,
                productName: true,
              },
            },
            supplier: {
              select: {
                supplierName: true,
              },
            },
          },
        },
        adjustedByUser: {
          select: {
            username: true,
            fullName: true,
          },
        },
      },
      orderBy: { createdAt: 'desc' },
    });

    return movements;
  }

  async getInventoryValue(supplierId?: number) {
    const where: any = {};
    if (supplierId) {
      where.supplierId = supplierId;
    }

    const result = await prisma.productStock.aggregate({
      where,
      _sum: {
        stockValue: true,
        quantityAvailable: true,
      },
      _count: {
        id: true,
      },
    });

    const lowStockItems = await prisma.productStock.count({
      where: {
        ...where,
        quantityAvailable: { lte: prisma.productStock.fields.reorderLevel },
      },
    });

    const outOfStockItems = await prisma.productStock.count({
      where: {
        ...where,
        quantityAvailable: 0,
      },
    });

    return {
      totalValue: Number(result._sum.stockValue) || 0,
      totalQuantity: result._sum.quantityAvailable || 0,
      totalItems: result._count.id,
      lowStockItems,
      outOfStockItems,
      averageValuePerItem: result._count.id > 0 ? 
        (Number(result._sum.stockValue) || 0) / result._count.id : 0,
    };
  }

  private calculateRestockStatus(
    currentStock: number,
    reorderLevel: number,
    quantityOnOrder: number
  ): string {
    if (currentStock === 0) return 'urgent';
    if (currentStock <= reorderLevel && quantityOnOrder === 0) return 'recommended';
    if (currentStock <= reorderLevel && quantityOnOrder > 0) return 'ordered';
    return 'not_needed';
  }

  private determineStockLevel(currentStock: number, reorderLevel: number): string {
    if (currentStock === 0) return 'out_of_stock';
    if (currentStock <= reorderLevel) return 'low_stock';
    if (currentStock >= reorderLevel * 3) return 'overstock';
    return 'in_stock';
  }

  private calculateDaysOfStock(currentStock: number, averageSalesPerMonth: number): number {
    if (averageSalesPerMonth === 0) return 999;
    return Math.floor((currentStock / averageSalesPerMonth) * 30);
  }
}
```

### 6. Database Schema Updates
```prisma
// Add to existing schema in prisma/schema.prisma

model ProductCategory {
  id          Int      @id @default(autoincrement())
  name        String   @unique @db.VarChar(100)
  description String?  @db.Text
  parentId    Int?     @map("parent_id")
  isActive    Boolean  @default(true) @map("is_active")
  createdAt   DateTime @default(now()) @map("created_at")
  updatedAt   DateTime @updatedAt @map("updated_at")

  // Relations
  parent      ProductCategory? @relation("CategoryHierarchy", fields: [parentId], references: [id])
  children    ProductCategory[] @relation("CategoryHierarchy")
  products    Product[]

  @@map("product_categories")
}

model Supplier {
  id             Int      @id @default(autoincrement())
  supplierName   String   @map("supplier_name") @db.VarChar(255)
  contactName    String?  @map("contact_name") @db.VarChar(255)
  contactEmail   String?  @map("contact_email") @db.VarChar(255)
  contactPhone   String?  @map("contact_phone") @db.VarChar(50)
  address        String?  @db.Text // JSON
  website        String?  @db.VarChar(255)
  paymentTerms   String?  @map("payment_terms") @db.VarChar(255)
  shippingTerms  String?  @map("shipping_terms") @db.VarChar(255)
  taxId          String?  @map("tax_id") @db.VarChar(50)
  notes          String?  @db.Text
  rating         Int      @default(3) @db.SmallInt
  status         String   @default("active") @db.VarChar(20)
  createdBy      Int      @map("created_by")
  createdAt      DateTime @default(now()) @map("created_at")
  updatedAt      DateTime @updatedAt @map("updated_at")

  // Relations
  createdByUser  User           @relation(fields: [createdBy], references: [id])
  products       Product[]
  productStock   ProductStock[]
  purchaseOrders PurchaseOrder[]

  @@map("suppliers")
}

model Product {
  id              Int      @id @default(autoincrement())
  sku             String   @unique @db.VarChar(100)
  productName     String   @map("product_name") @db.VarChar(255)
  supplierId      Int      @map("supplier_id")
  categoryId      Int?     @map("category_id")
  description     String?  @db.Text
  costPrice       Decimal  @map("cost_price") @db.Decimal(10, 2)
  suggestedPrice  Decimal  @map("suggested_price") @db.Decimal(10, 2)
  weight          Decimal? @db.Decimal(8, 3)
  dimensions      String?  @db.VarChar(100)
  images          String?  @db.Text // JSON array
  tags            String?  @db.Text // JSON array
  barcode         String?  @db.VarChar(50)
  isbn            String?  @db.VarChar(20)
  upc             String?  @db.VarChar(20)
  ean             String?  @db.VarChar(20)
  status          String   @default("active") @db.VarChar(20)
  createdBy       Int      @map("created_by")
  createdAt       DateTime @default(now()) @map("created_at")
  updatedAt       DateTime @updatedAt @map("updated_at")

  // Relations
  supplier        Supplier         @relation(fields: [supplierId], references: [id])
  category        ProductCategory? @relation(fields: [categoryId], references: [id])
  createdByUser   User            @relation(fields: [createdBy], references: [id])
  stock           ProductStock[]
  listings        Listing[]       @relation("ProductToListing")
  orderItems      OrderItem[]     @relation("ProductToOrderItem")

  @@map("products")
}

model ProductStock {
  id                    Int      @id @default(autoincrement())
  productId             Int      @map("product_id")
  supplierId            Int      @map("supplier_id")
  quantityAvailable     Int      @default(0) @map("quantity_available")
  quantityReserved      Int      @default(0) @map("quantity_reserved")
  quantityOnOrder       Int      @default(0) @map("quantity_on_order")
  reorderLevel          Int      @default(10) @map("reorder_level")
  reorderQuantity       Int      @default(50) @map("reorder_quantity")
  maxStockLevel         Int      @default(200) @map("max_stock_level")
  lastRestockDate       DateTime? @map("last_restock_date")
  nextRestockDate       DateTime? @map("next_restock_date")
  restockStatus         String   @default("not_needed") @map("restock_status") @db.VarChar(20)
  averageSalesPerMonth  Decimal  @default(0) @map("average_sales_per_month") @db.Decimal(8, 2)
  stockValue            Decimal  @default(0) @map("stock_value") @db.Decimal(12, 2)
  lastUpdated           DateTime @default(now()) @map("last_updated")

  // Relations
  product               Product            @relation(fields: [productId], references: [id], onDelete: Cascade)
  supplier              Supplier           @relation(fields: [supplierId], references: [id])
  adjustments           StockAdjustment[]
  reservations          StockReservation[]

  @@unique([productId, supplierId])
  @@map("product_stock")
}

model StockAdjustment {
  id                 Int          @id @default(autoincrement())
  productStockId     Int          @map("product_stock_id")
  adjustmentQuantity Int          @map("adjustment_quantity")
  previousQuantity   Int          @map("previous_quantity")
  newQuantity        Int          @map("new_quantity")
  reason             String       @db.VarChar(255)
  adjustedBy         Int          @map("adjusted_by")
  createdAt          DateTime     @default(now()) @map("created_at")

  // Relations
  productStock       ProductStock @relation(fields: [productStockId], references: [id], onDelete: Cascade)
  adjustedByUser     User         @relation(fields: [adjustedBy], references: [id])

  @@map("stock_adjustments")
}

model StockReservation {
  id               Int          @id @default(autoincrement())
  productStockId   Int          @map("product_stock_id")
  reservedQuantity Int          @map("reserved_quantity")
  reservedBy       Int          @map("reserved_by")
  status           String       @default("active") @db.VarChar(20)
  expiresAt        DateTime     @map("expires_at")
  releasedAt       DateTime?    @map("released_at")
  createdAt        DateTime     @default(now()) @map("created_at")

  // Relations
  productStock     ProductStock @relation(fields: [productStockId], references: [id], onDelete: Cascade)
  reservedByUser   User         @relation(fields: [reservedBy], references: [id])

  @@map("stock_reservations")
}

model PurchaseOrder {
  id              Int      @id @default(autoincrement())
  supplierId      Int      @map("supplier_id")
  orderNumber     String   @unique @map("order_number") @db.VarChar(50)
  totalAmount     Decimal  @map("total_amount") @db.Decimal(12, 2)
  currency        String   @default("USD") @db.VarChar(3)
  status          String   @default("pending") @db.VarChar(20)
  orderDate       DateTime @map("order_date")
  expectedDate    DateTime? @map("expected_date")
  deliveredAt     DateTime? @map("delivered_at")
  notes           String?  @db.Text
  createdBy       Int      @map("created_by")
  createdAt       DateTime @default(now()) @map("created_at")
  updatedAt       DateTime @updatedAt @map("updated_at")

  // Relations
  supplier        Supplier           @relation(fields: [supplierId], references: [id])
  createdByUser   User              @relation(fields: [createdBy], references: [id])
  items           PurchaseOrderItem[]

  @@map("purchase_orders")
}

model PurchaseOrderItem {
  id              Int           @id @default(autoincrement())
  purchaseOrderId Int           @map("purchase_order_id")
  productId       Int           @map("product_id")
  quantity        Int
  unitCost        Decimal       @map("unit_cost") @db.Decimal(10, 2)
  totalCost       Decimal       @map("total_cost") @db.Decimal(10, 2)
  receivedQuantity Int          @default(0) @map("received_quantity")

  // Relations
  purchaseOrder   PurchaseOrder @relation(fields: [purchaseOrderId], references: [id], onDelete: Cascade)
  product         Product       @relation(fields: [productId], references: [id])

  @@map("purchase_order_items")
}

// Update existing models to include new relations
model User {
  // ... existing fields ...
  
  // Relations
  ebayAccounts        EbayAccount[]
  accountPermissions  UserAccountPermission[]
  assignedPermissions UserAccountPermission[] @relation("AssignedBy")
  orderStatusUpdates  OrderStatusHistory[]
  draftListings       DraftListing[]
  listingHistory      ListingHistory[]
  suppliers           Supplier[]
  products            Product[]
  stockAdjustments    StockAdjustment[]
  stockReservations   StockReservation[]
  purchaseOrders      PurchaseOrder[]

  @@map("users")
}

// Update Listing model to include product relation
model Listing {
  // ... existing fields ...
  productId           Int?     @map("product_id")
  
  // Relations
  account             EbayAccount   @relation(fields: [ebayAccountId], references: [id], onDelete: Cascade)
  orderItems          OrderItem[]
  listingHistory      ListingHistory[]
  product             Product?      @relation("ProductToListing", fields: [productId], references: [id])

  @@unique([itemNumber, ebayAccountId])
  @@map("listings")
}

// Update OrderItem model to include product relation
model OrderItem {
  // ... existing fields ...
  productId           Int?     @map("product_id")
  
  // Relations
  order               Order    @relation(fields: [orderId], references: [id], onDelete: Cascade)
  listing             Listing? @relation(fields: [itemNumber, accountId], references: [itemNumber, ebayAccountId])
  product             Product? @relation("ProductToOrderItem", fields: [productId], references: [id])

  @@map("order_items")
}
```

### 7. Controllers & Routes Implementation
```typescript
// src/controllers/product.controller.ts
import { Request, Response } from 'express';
import { ProductService } from '../services/product.service';
import { InventoryService } from '../services/inventory.service';
import {
  createProductSchema,
  updateProductSchema,
  productFilterSchema,
  bulkProductUpdateSchema,
} from '../schemas/product.schema';
import { ApiResponse } from '../types/common.types';

const productService = new ProductService();
const inventoryService = new InventoryService();

export class ProductController {
  async getProducts(req: Request, res: Response<ApiResponse>) {
    try {
      const page = parseInt(req.query.page as string) || 1;
      const limit = parseInt(req.query.limit as string) || 20;
      const sortBy = req.query.sortBy as string || 'productName';
      const sortOrder = (req.query.sortOrder as 'asc' | 'desc') || 'asc';
      
      const filters = productFilterSchema.parse({
        supplierId: req.query.supplierId ? parseInt(req.query.supplierId as string) : undefined,
        categoryId: req.query.categoryId ? parseInt(req.query.categoryId as string) : undefined,
        sku: req.query.sku as string,
        productName: req.query.productName as string,
        priceRange: req.query.minPrice && req.query.maxPrice ? {
          min: parseFloat(req.query.minPrice as string),
          max: parseFloat(req.query.maxPrice as string),
        } : undefined,
        stockLevel: req.query.stockLevel ? (req.query.stockLevel as string).split(',') : undefined,
        status: req.query.status ? (req.query.status as string).split(',') : undefined,
        profitMargin: req.query.minMargin && req.query.maxMargin ? {
          min: parseFloat(req.query.minMargin as string),
          max: parseFloat(req.query.maxMargin as string),
        } : undefined,
      });
      
      const result = await productService.getProducts(
        { page, limit, sortBy, sortOrder },
        filters
      );
      
      res.json({
        success: true,
        data: result.products,
        meta: result.pagination,
      });
    } catch (error) {
      res.status(500).json({
        success: false,
        error: error instanceof Error ? error.message : 'Failed to get products',
      });
    }
  }

  async getProductById(req: Request, res: Response<ApiResponse>) {
    try {
      const productId = parseInt(req.params.id);
      const product = await productService.getProductById(productId);
      
      res.json({
        success: true,
        data: product,
      });
    } catch (error) {
      res.status(404).json({
        success: false,
        error: error instanceof Error ? error.message : 'Product not found',
      });
    }
  }

  async createProduct(req: Request, res: Response<ApiResponse>) {
    try {
      const validatedData = createProductSchema.parse(req.body);
      const userId = req.user?.userId;
      
      if (!userId) {
        return res.status(401).json({
          success: false,
          error: 'User not authenticated',
        });
      }
      
      const product = await productService.createProduct(validatedData, userId);
      
      res.status(201).json({
        success: true,
        data: product,
        message: 'Product created successfully',
      });
    } catch (error) {
      res.status(400).json({
        success: false,
        error: error instanceof Error ? error.message : 'Failed to create product',
      });
    }
  }

  async updateProduct(req: Request, res: Response<ApiResponse>) {
    try {
      const productId = parseInt(req.params.id);
      const validatedData = updateProductSchema.parse(req.body);
      
      const product = await productService.updateProduct(productId, validatedData);
      
      res.json({
        success: true,
        data: product,
        message: 'Product updated successfully',
      });
    } catch (error) {
      res.status(400).json({
        success: false,
        error: error instanceof Error ? error.message : 'Failed to update product',
      });
    }
  }

  async bulkUpdateProducts(req: Request, res: Response<ApiResponse>) {
    try {
      const validatedData = bulkProductUpdateSchema.parse(req.body);
      const userId = req.user?.userId;
      
      if (!userId) {
        return res.status(401).json({
          success: false,
          error: 'User not authenticated',
        });
      }
      
      const result = await productService.bulkUpdateProducts(
        validatedData.productIds,
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

  async getRestockRecommendations(req: Request, res: Response<ApiResponse>) {
    try {
      const supplierId = req.query.supplierId ? parseInt(req.query.supplierId as string) : undefined;
      
      const recommendations = await productService.getRestockRecommendations(supplierId);
      
      res.json({
        success: true,
        data: recommendations,
        meta: { count: recommendations.length },
      });
    } catch (error) {
      res.status(500).json({
        success: false,
        error: error instanceof Error ? error.message : 'Failed to get restock recommendations',
      });
    }
  }

  async searchProducts(req: Request, res: Response<ApiResponse>) {
    try {
      const query = req.query.q as string;
      const limit = parseInt(req.query.limit as string) || 20;
      
      if (!query || query.trim().length < 2) {
        return res.status(400).json({
          success: false,
          error: 'Search query must be at least 2 characters',
        });
      }
      
      const results = await productService.searchProducts(query.trim(), limit);
      
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

  async getProductAnalytics(req: Request, res: Response<ApiResponse>) {
    try {
      const productId = parseInt(req.params.id);
      const dateRange = req.query.startDate && req.query.endDate ? {
        start: new Date(req.query.startDate as string),
        end: new Date(req.query.endDate as string),
      } : undefined;
      
      const analytics = await productService.getProductAnalytics(productId, dateRange);
      
      res.json({
        success: true,
        data: analytics,
      });
    } catch (error) {
      res.status(500).json({
        success: false,
        error: error instanceof Error ? error.message : 'Failed to get product analytics',
      });
    }
  }
}
```

### 8. API Routes
```typescript
// src/routes/product.routes.ts
import { Router } from 'express';
import { ProductController } from '../controllers/product.controller';
import { SupplierController } from '../controllers/supplier.controller';
import { InventoryController } from '../controllers/inventory.controller';
import { authenticate, authorize } from '../middleware/auth.middleware';

const router = Router();
const productController = new ProductController();
const supplierController = new SupplierController();
const inventoryController = new InventoryController();

// All routes require authentication
router.use(authenticate);

// Product routes
router.get('/products', productController.getProducts.bind(productController));
router.get('/products/search', productController.searchProducts.bind(productController));
router.get('/products/restock-recommendations', productController.getRestockRecommendations.bind(productController));
router.get('/products/:id', productController.getProductById.bind(productController));
router.get('/products/:id/analytics', productController.getProductAnalytics.bind(productController));
router.post('/products', productController.createProduct.bind(productController));
router.put('/products/:id', productController.updateProduct.bind(productController));
router.post('/products/bulk-update', productController.bulkUpdateProducts.bind(productController));

// Supplier routes
router.get('/suppliers', supplierController.getSuppliers.bind(supplierController));
router.get('/suppliers/statistics', supplierController.getSupplierStatistics.bind(supplierController));
router.get('/suppliers/:id', supplierController.getSupplierById.bind(supplierController));
router.get('/suppliers/:id/performance', supplierController.getSupplierPerformance.bind(supplierController));
router.post('/suppliers', authorize(['super_admin', 'manager']), supplierController.createSupplier.bind(supplierController));
router.put('/suppliers/:id', authorize(['super_admin', 'manager']), supplierController.updateSupplier.bind(supplierController));
router.patch('/suppliers/:id/toggle-status', authorize(['super_admin', 'manager']), supplierController.toggleSupplierStatus.bind(supplierController));

// Inventory routes
router.get('/inventory', inventoryController.getInventoryReport.bind(inventoryController));
router.get('/inventory/value', inventoryController.getInventoryValue.bind(inventoryController));
router.get('/inventory/movements', inventoryController.getStockMovements.bind(inventoryController));
router.post('/inventory/adjust', inventoryController.adjustStock.bind(inventoryController));
router.post('/inventory/reserve', inventoryController.reserveStock.bind(inventoryController));
router.post('/inventory/release/:reservationId', inventoryController.releaseReservation.bind(inventoryController));

export default router;
```

## Success Criteria

1. ✅ Comprehensive product management with SKU tracking
2. ✅ Supplier management with performance analytics
3. ✅ Inventory tracking with stock levels and alerts
4. ✅ Restock recommendations based on sales velocity
5. ✅ Cost analysis and profit margin calculations
6. ✅ Stock reservations and adjustments
7. ✅ Purchase order management
8. ✅ Bulk operations for products and inventory
9. ✅ Product analytics and performance tracking
10. ✅ Supplier comparison and rating system

## Next Steps
- Plan 7: Customer Management & Communication Module
- Plan 8: Frontend Dashboard Implementation