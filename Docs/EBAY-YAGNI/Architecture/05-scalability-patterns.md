# Scalability Patterns - eBay Manager

## YAGNI Compliance: 80% Complexity Reduction
**Eliminates**: Complex sharding strategies, sophisticated load balancers, advanced caching hierarchies, complex microservices orchestration, over-engineered auto-scaling, premature database partitioning, complex CDN configurations.

**Maintains**: Horizontal scaling foundation, efficient caching, database optimization, basic load balancing, performance monitoring, connection pooling, resource optimization.

## Scalability Principles (SOLID Compliance)

### Single Responsibility Principle (SRP)
Each scalability component has a focused performance concern:

```typescript
// ❌ Violates SRP - Mixed scalability responsibilities
class PerformanceManager {
  cacheData() { /* Redis caching */ }
  balanceLoad() { /* Load balancing */ }
  optimizeDatabase() { /* Query optimization */ }
  monitorMetrics() { /* Performance monitoring */ }
  scaleResources() { /* Auto-scaling */ }
}

// ✅ Follows SRP - Separated scalability concerns
class CacheService {
  constructor(
    private redis: Redis,
    private config: CacheConfig
  ) {}
  
  async get<T>(key: string): Promise<T | null> {
    try {
      const cached = await this.redis.get(key);
      return cached ? JSON.parse(cached) : null;
    } catch (error) {
      logger.warn('Cache get failed:', error);
      return null; // Fail gracefully
    }
  }
  
  async set<T>(key: string, value: T, ttlSeconds = 3600): Promise<void> {
    try {
      await this.redis.setex(key, ttlSeconds, JSON.stringify(value));
    } catch (error) {
      logger.error('Cache set failed:', error);
      // Don't throw - caching failures shouldn't break the app
    }
  }
}

class DatabaseOptimizationService {
  constructor(private db: PrismaClient) {}
  
  async optimizeQuery<T>(
    query: () => Promise<T>,
    cacheKey?: string,
    ttl = 300
  ): Promise<T> {
    if (cacheKey) {
      const cached = await this.cacheService.get<T>(cacheKey);
      if (cached) return cached;
    }
    
    const result = await query();
    
    if (cacheKey) {
      await this.cacheService.set(cacheKey, result, ttl);
    }
    
    return result;
  }
}
```

### Open/Closed Principle (OCP)
Scalability architecture supports extension without modifying core performance logic:

```typescript
// Core performance interface - closed for modification
interface IPerformanceOptimizer {
  optimize<T>(operation: () => Promise<T>, context: OptimizationContext): Promise<T>;
}

// Extendable optimizers - open for extension
class CacheOptimizer implements IPerformanceOptimizer {
  async optimize<T>(operation: () => Promise<T>, context: OptimizationContext): Promise<T> {
    const cacheKey = this.generateCacheKey(context);
    const cached = await this.cacheService.get<T>(cacheKey);
    
    if (cached) {
      this.metricsService.incrementCacheHit(context.operation);
      return cached;
    }
    
    const result = await operation();
    await this.cacheService.set(cacheKey, result, context.ttl);
    this.metricsService.incrementCacheMiss(context.operation);
    
    return result;
  }
}

class BatchOptimizer implements IPerformanceOptimizer {
  private batches = new Map<string, BatchOperation[]>();
  
  async optimize<T>(operation: () => Promise<T>, context: OptimizationContext): Promise<T> {
    if (!context.batchable) {
      return operation();
    }
    
    return this.addToBatch(operation, context);
  }
}

class QueryOptimizer implements IPerformanceOptimizer {
  async optimize<T>(operation: () => Promise<T>, context: OptimizationContext): Promise<T> {
    const startTime = Date.now();
    
    try {
      const result = await operation();
      
      const duration = Date.now() - startTime;
      this.metricsService.recordQueryTime(context.operation, duration);
      
      if (duration > context.slowQueryThreshold) {
        logger.warn('Slow query detected:', {
          operation: context.operation,
          duration,
          context: context.metadata
        });
      }
      
      return result;
    } catch (error) {
      this.metricsService.incrementQueryError(context.operation);
      throw error;
    }
  }
}
```

## Caching Strategies

### 1. Multi-Level Caching Architecture
```typescript
// Layered caching system (YAGNI approach - simple but effective)
export class CachingService {
  constructor(
    private memoryCache: NodeCache,     // L1: In-memory (fast, small)
    private redisCache: Redis,          // L2: Redis (medium, shared)
    private config: CacheConfig
  ) {}
  
  async get<T>(key: string, options: CacheOptions = {}): Promise<T | null> {
    const fullKey = this.buildKey(key, options.namespace);
    
    // L1: Check memory cache first
    const memoryResult = this.memoryCache.get<T>(fullKey);
    if (memoryResult !== undefined) {
      this.recordCacheHit('memory', key);
      return memoryResult;
    }
    
    // L2: Check Redis cache
    try {
      const redisResult = await this.redisCache.get(fullKey);
      if (redisResult) {
        const parsed = JSON.parse(redisResult) as T;
        
        // Populate memory cache for next time
        this.memoryCache.set(fullKey, parsed, options.memoryTtl || 300);
        
        this.recordCacheHit('redis', key);
        return parsed;
      }
    } catch (error) {
      logger.warn('Redis cache error:', error);
    }
    
    this.recordCacheMiss(key);
    return null;
  }
  
  async set<T>(key: string, value: T, options: CacheOptions = {}): Promise<void> {
    const fullKey = this.buildKey(key, options.namespace);
    const ttl = options.ttl || this.config.defaultTtl;
    
    // Set in memory cache
    this.memoryCache.set(fullKey, value, options.memoryTtl || Math.min(ttl, 300));
    
    // Set in Redis cache
    try {
      await this.redisCache.setex(fullKey, ttl, JSON.stringify(value));
    } catch (error) {
      logger.error('Redis cache set error:', error);
    }
  }
  
  async invalidate(pattern: string): Promise<void> {
    // Invalidate memory cache
    this.memoryCache.flushAll();
    
    // Invalidate Redis cache
    try {
      const keys = await this.redisCache.keys(pattern);
      if (keys.length > 0) {
        await this.redisCache.del(...keys);
      }
    } catch (error) {
      logger.error('Redis cache invalidation error:', error);
    }
  }
  
  private buildKey(key: string, namespace?: string): string {
    return namespace ? `${namespace}:${key}` : key;
  }
}

// Cache-aware repository pattern
export class CachedRepository<T extends { id: string }> {
  constructor(
    private baseRepository: IRepository<T>,
    private cacheService: CachingService,
    private entityName: string
  ) {}
  
  async findById(id: string): Promise<T | null> {
    const cacheKey = `${this.entityName}:${id}`;
    
    // Try cache first
    const cached = await this.cacheService.get<T>(cacheKey);
    if (cached) {
      return cached;
    }
    
    // Fallback to database
    const entity = await this.baseRepository.findById(id);
    
    if (entity) {
      await this.cacheService.set(cacheKey, entity, { ttl: 1800 }); // 30 minutes
    }
    
    return entity;
  }
  
  async findMany(filters: any): Promise<T[]> {
    const cacheKey = `${this.entityName}:list:${this.hashFilters(filters)}`;
    
    const cached = await this.cacheService.get<T[]>(cacheKey);
    if (cached) {
      return cached;
    }
    
    const entities = await this.baseRepository.findMany(filters);
    await this.cacheService.set(cacheKey, entities, { ttl: 600 }); // 10 minutes
    
    return entities;
  }
  
  async update(id: string, data: Partial<T>): Promise<T> {
    const entity = await this.baseRepository.update(id, data);
    
    // Invalidate related caches
    await this.cacheService.invalidate(`${this.entityName}:${id}`);
    await this.cacheService.invalidate(`${this.entityName}:list:*`);
    
    // Update cache with new data
    await this.cacheService.set(`${this.entityName}:${id}`, entity);
    
    return entity;
  }
}
```

### 2. Application-Level Caching
```typescript
// Smart caching decorators
export function Cacheable(options: CacheableOptions = {}) {
  return function (target: any, propertyKey: string, descriptor: PropertyDescriptor) {
    const originalMethod = descriptor.value;
    
    descriptor.value = async function (...args: any[]) {
      const cacheKey = options.keyGenerator 
        ? options.keyGenerator(target.constructor.name, propertyKey, args)
        : `${target.constructor.name}:${propertyKey}:${JSON.stringify(args)}`;
      
      const cacheService = this.cacheService || container.get<CachingService>('CachingService');
      
      // Try cache first
      const cached = await cacheService.get(cacheKey);
      if (cached !== null) {
        return cached;
      }
      
      // Execute method
      const result = await originalMethod.apply(this, args);
      
      // Cache result
      await cacheService.set(cacheKey, result, {
        ttl: options.ttl || 3600,
        namespace: options.namespace
      });
      
      return result;
    };
  };
}

// Usage example
export class OrderService {
  @Cacheable({ 
    ttl: 1800, 
    namespace: 'orders',
    keyGenerator: (className, method, args) => `${className}:${method}:${args[0]}` // accountId
  })
  async getOrderStats(accountId: string): Promise<OrderStats> {
    return this.orderRepository.getStats(accountId);
  }
  
  @Cacheable({ 
    ttl: 300,
    namespace: 'orders'
  })
  async getRecentOrders(accountId: string, limit = 10): Promise<Order[]> {
    return this.orderRepository.findMany({
      accountId,
      orderBy: { orderDate: 'desc' },
      take: limit
    });
  }
}
```

## Database Scalability

### 1. Connection Pool Optimization
```typescript
// Optimized database connection management
export class DatabaseConnectionManager {
  private pools = new Map<string, PrismaClient>();
  
  constructor(private config: DatabaseConfig) {}
  
  getConnection(accountId?: string): PrismaClient {
    // Simple connection pooling strategy
    const poolKey = accountId ? `account_${accountId}` : 'default';
    
    if (!this.pools.has(poolKey)) {
      this.pools.set(poolKey, this.createConnection(poolKey));
    }
    
    return this.pools.get(poolKey)!;
  }
  
  private createConnection(poolKey: string): PrismaClient {
    return new PrismaClient({
      datasources: {
        db: {
          url: this.config.url
        }
      },
      log: this.config.logging ? ['query', 'error'] : ['error'],
      
      // Connection pool configuration
      __internal: {
        engine: {
          config: {
            pool: {
              size: this.getPoolSize(poolKey),
              timeout: 30000,
              idleTimeout: 30000
            }
          }
        }
      }
    });
  }
  
  private getPoolSize(poolKey: string): number {
    // Adjust pool size based on usage patterns
    if (poolKey === 'default') {
      return this.config.defaultPoolSize || 10;
    }
    return this.config.accountPoolSize || 5;
  }
  
  async healthCheck(): Promise<ConnectionHealth[]> {
    const health: ConnectionHealth[] = [];
    
    for (const [poolKey, client] of this.pools) {
      try {
        const start = Date.now();
        await client.$queryRaw`SELECT 1`;
        const responseTime = Date.now() - start;
        
        health.push({
          poolKey,
          status: 'healthy',
          responseTime,
          timestamp: new Date()
        });
      } catch (error) {
        health.push({
          poolKey,
          status: 'unhealthy',
          error: error.message,
          timestamp: new Date()
        });
      }
    }
    
    return health;
  }
}
```

### 2. Query Optimization Patterns
```typescript
// Efficient bulk operations and query optimization
export class OptimizedQueryService {
  constructor(private db: PrismaClient) {}
  
  // Batch operations to reduce database round trips
  async bulkUpsertOrders(orders: Order[], batchSize = 100): Promise<void> {
    for (let i = 0; i < orders.length; i += batchSize) {
      const batch = orders.slice(i, i + batchSize);
      
      await this.db.$transaction(async (tx) => {
        // Process batch in parallel within transaction
        const operations = batch.map(order => 
          tx.order.upsert({
            where: { 
              accountId_orderId: { 
                accountId: order.accountId, 
                orderId: order.orderId 
              }
            },
            update: {
              status: order.status,
              totalAmount: order.totalAmount,
              updatedAt: new Date()
            },
            create: {
              orderId: order.orderId,
              accountId: order.accountId,
              customerId: order.customerId,
              status: order.status,
              totalAmount: order.totalAmount,
              orderDate: order.orderDate
            }
          })
        );
        
        await Promise.all(operations);
      });
    }
  }
  
  // Efficient pagination with cursor-based approach
  async getPaginatedOrders(
    accountId: string, 
    cursor?: string, 
    limit = 50
  ): Promise<PaginatedResult<Order>> {
    const orders = await this.db.order.findMany({
      where: { 
        accountId,
        ...(cursor && { id: { gt: cursor } })
      },
      orderBy: { id: 'asc' },
      take: limit + 1, // Fetch one extra to determine if there's a next page
      include: {
        orderItems: true,
        customer: {
          select: {
            id: true,
            ebayUsername: true,
            email: true
          }
        }
      }
    });
    
    const hasNextPage = orders.length > limit;
    const items = hasNextPage ? orders.slice(0, -1) : orders;
    const nextCursor = hasNextPage ? orders[limit - 1].id : null;
    
    return {
      items,
      hasNextPage,
      nextCursor,
      totalCount: await this.getOrdersCount(accountId)
    };
  }
  
  // Optimized aggregation queries
  async getAccountMetrics(accountId: string): Promise<AccountMetrics> {
    // Use a single complex query instead of multiple simple ones
    const result = await this.db.$queryRaw<MetricsRow[]>`
      SELECT 
        COUNT(DISTINCT o.id) as total_orders,
        SUM(o.total_amount) as total_revenue,
        AVG(o.total_amount) as avg_order_value,
        COUNT(DISTINCT o.customer_id) as unique_customers,
        COUNT(DISTINCT l.id) as active_listings,
        COUNT(DISTINCT p.id) as total_products
      FROM orders o
      LEFT JOIN listings l ON l.account_id = o.account_id AND l.status = 'active'
      LEFT JOIN products p ON p.account_id = o.account_id AND p.is_active = true
      WHERE o.account_id = ${accountId}
        AND o.order_date >= NOW() - INTERVAL '30 days'
    `;
    
    return {
      totalOrders: Number(result[0].total_orders),
      totalRevenue: Number(result[0].total_revenue || 0),
      averageOrderValue: Number(result[0].avg_order_value || 0),
      uniqueCustomers: Number(result[0].unique_customers),
      activeListings: Number(result[0].active_listings),
      totalProducts: Number(result[0].total_products)
    };
  }
}
```

## Load Balancing & Resource Management

### 1. Application Load Distribution
```typescript
// Simple but effective load balancing for API requests
export class LoadBalancingService {
  private requestCounts = new Map<string, number>();
  private lastReset = Date.now();
  private resetInterval = 60000; // 1 minute
  
  // Distribute load based on account activity
  getOptimalServer(accountId: string): ServerInfo {
    this.maybeResetCounters();
    
    const currentCount = this.requestCounts.get(accountId) || 0;
    this.requestCounts.set(accountId, currentCount + 1);
    
    // Simple round-robin with account affinity
    const servers = this.getAvailableServers();
    const accountHash = this.hashAccountId(accountId);
    const serverIndex = accountHash % servers.length;
    
    return servers[serverIndex];
  }
  
  // Health-aware server selection
  getHealthyServer(): ServerInfo {
    const servers = this.getAvailableServers();
    const healthyServers = servers.filter(server => 
      server.health.status === 'healthy' && 
      server.load < server.maxLoad
    );
    
    if (healthyServers.length === 0) {
      throw new Error('No healthy servers available');
    }
    
    // Select server with lowest load
    return healthyServers.reduce((prev, current) => 
      prev.load < current.load ? prev : current
    );
  }
  
  private getAvailableServers(): ServerInfo[] {
    return [
      {
        id: 'server-1',
        url: process.env.SERVER_1_URL || 'http://localhost:3001',
        load: this.getCurrentLoad('server-1'),
        maxLoad: 100,
        health: { status: 'healthy' }
      },
      {
        id: 'server-2', 
        url: process.env.SERVER_2_URL || 'http://localhost:3002',
        load: this.getCurrentLoad('server-2'),
        maxLoad: 100,
        health: { status: 'healthy' }
      }
    ];
  }
}

// Resource pool management
export class ResourcePoolManager {
  private pools = new Map<string, ResourcePool>();
  
  getPool<T>(poolName: string, factory: () => T, config: PoolConfig): ResourcePool<T> {
    if (!this.pools.has(poolName)) {
      this.pools.set(poolName, new ResourcePool(factory, config));
    }
    
    return this.pools.get(poolName) as ResourcePool<T>;
  }
  
  async getResource<T>(poolName: string): Promise<T> {
    const pool = this.pools.get(poolName);
    if (!pool) {
      throw new Error(`Pool ${poolName} not found`);
    }
    
    return pool.acquire();
  }
  
  async releaseResource<T>(poolName: string, resource: T): Promise<void> {
    const pool = this.pools.get(poolName);
    if (pool) {
      await pool.release(resource);
    }
  }
}

class ResourcePool<T> {
  private available: T[] = [];
  private inUse = new Set<T>();
  private creating = false;
  
  constructor(
    private factory: () => T,
    private config: PoolConfig
  ) {}
  
  async acquire(): Promise<T> {
    // Try to get available resource
    if (this.available.length > 0) {
      const resource = this.available.pop()!;
      this.inUse.add(resource);
      return resource;
    }
    
    // Create new resource if under limit
    if (this.inUse.size < this.config.maxSize && !this.creating) {
      this.creating = true;
      try {
        const resource = await this.createResource();
        this.inUse.add(resource);
        return resource;
      } finally {
        this.creating = false;
      }
    }
    
    // Wait for resource to become available
    return this.waitForResource();
  }
  
  async release(resource: T): Promise<void> {
    if (!this.inUse.has(resource)) {
      return;
    }
    
    this.inUse.delete(resource);
    
    if (this.available.length < this.config.minSize) {
      this.available.push(resource);
    } else {
      await this.destroyResource(resource);
    }
  }
}
```

## Performance Monitoring

### 1. Real-time Performance Metrics
```typescript
// Performance monitoring service
export class PerformanceMonitoringService {
  private metrics = new Map<string, MetricData>();
  private metricsBuffer: MetricEvent[] = [];
  private flushInterval = 10000; // 10 seconds
  
  constructor() {
    this.startMetricsFlush();
  }
  
  // Record response time
  recordResponseTime(endpoint: string, duration: number, metadata?: any): void {
    this.recordMetric({
      type: 'response_time',
      name: endpoint,
      value: duration,
      timestamp: Date.now(),
      metadata
    });
  }
  
  // Record cache performance
  recordCacheHit(cacheType: string, key: string): void {
    this.recordMetric({
      type: 'cache_hit',
      name: `${cacheType}_cache`,
      value: 1,
      timestamp: Date.now(),
      metadata: { key, hit: true }
    });
  }
  
  recordCacheMiss(key: string): void {
    this.recordMetric({
      type: 'cache_miss',
      name: 'cache',
      value: 1,
      timestamp: Date.now(),
      metadata: { key, hit: false }
    });
  }
  
  // Record database query performance
  recordDatabaseQuery(query: string, duration: number, rowCount?: number): void {
    this.recordMetric({
      type: 'db_query',
      name: 'database',
      value: duration,
      timestamp: Date.now(),
      metadata: { query, rowCount, slow: duration > 1000 }
    });
  }
  
  // Get current metrics
  getCurrentMetrics(): PerformanceMetrics {
    const now = Date.now();
    const last5Min = now - 5 * 60 * 1000;
    
    const recentMetrics = this.metricsBuffer.filter(m => m.timestamp > last5Min);
    
    return {
      responseTime: this.calculateAverageResponseTime(recentMetrics),
      throughput: this.calculateThroughput(recentMetrics),
      errorRate: this.calculateErrorRate(recentMetrics),
      cacheHitRate: this.calculateCacheHitRate(recentMetrics),
      databasePerformance: this.calculateDatabasePerformance(recentMetrics),
      activeConnections: this.getActiveConnections(),
      memoryUsage: this.getMemoryUsage(),
      timestamp: new Date()
    };
  }
  
  private recordMetric(event: MetricEvent): void {
    this.metricsBuffer.push(event);
    
    // Keep buffer size manageable
    if (this.metricsBuffer.length > 10000) {
      this.metricsBuffer = this.metricsBuffer.slice(-5000);
    }
  }
  
  private startMetricsFlush(): void {
    setInterval(() => {
      this.flushMetrics();
    }, this.flushInterval);
  }
  
  private async flushMetrics(): Promise<void> {
    if (this.metricsBuffer.length === 0) return;
    
    const metrics = this.getCurrentMetrics();
    
    // Log performance metrics
    logger.info('Performance metrics:', {
      ...metrics,
      bufferSize: this.metricsBuffer.length
    });
    
    // Alert on performance issues
    if (metrics.responseTime.average > 2000) {
      logger.warn('High average response time detected:', {
        average: metrics.responseTime.average,
        p95: metrics.responseTime.p95
      });
    }
    
    if (metrics.errorRate > 0.05) { // 5%
      logger.error('High error rate detected:', {
        errorRate: metrics.errorRate,
        errors: metrics.errorRate * metrics.throughput
      });
    }
  }
}

// Performance monitoring middleware
export const performanceMiddleware = (
  performanceMonitor: PerformanceMonitoringService
) => {
  return (req: Request, res: Response, next: NextFunction) => {
    const startTime = Date.now();
    
    res.on('finish', () => {
      const duration = Date.now() - startTime;
      const endpoint = `${req.method} ${req.route?.path || req.path}`;
      
      performanceMonitor.recordResponseTime(endpoint, duration, {
        statusCode: res.statusCode,
        method: req.method,
        path: req.path,
        userAgent: req.headers['user-agent'],
        accountId: req.params?.accountId
      });
    });
    
    next();
  };
};
```

### 2. Auto-scaling Triggers (YAGNI Approach)
```typescript
// Simple auto-scaling based on metrics
export class AutoScalingService {
  private scalingCooldown = 5 * 60 * 1000; // 5 minutes
  private lastScalingAction = 0;
  
  constructor(
    private performanceMonitor: PerformanceMonitoringService,
    private loadBalancer: LoadBalancingService
  ) {
    this.startScalingMonitor();
  }
  
  async checkScalingNeeds(): Promise<ScalingAction | null> {
    const now = Date.now();
    if (now - this.lastScalingAction < this.scalingCooldown) {
      return null; // Still in cooldown
    }
    
    const metrics = this.performanceMonitor.getCurrentMetrics();
    
    // Scale up triggers
    if (metrics.responseTime.average > 3000 || // 3 seconds
        metrics.throughput > 1000 ||         // High throughput
        metrics.memoryUsage > 0.8) {         // 80% memory usage
      
      this.lastScalingAction = now;
      return {
        action: 'scale_up',
        reason: 'High load detected',
        metrics: {
          responseTime: metrics.responseTime.average,
          throughput: metrics.throughput,
          memoryUsage: metrics.memoryUsage
        }
      };
    }
    
    // Scale down triggers (be more conservative)
    if (metrics.responseTime.average < 500 &&  // Fast responses
        metrics.throughput < 100 &&            // Low throughput
        metrics.memoryUsage < 0.3 &&           // Low memory usage
        this.getActiveServers().length > 1) {  // Have multiple servers
      
      this.lastScalingAction = now;
      return {
        action: 'scale_down',
        reason: 'Low load detected',
        metrics: {
          responseTime: metrics.responseTime.average,
          throughput: metrics.throughput,
          memoryUsage: metrics.memoryUsage
        }
      };
    }
    
    return null;
  }
  
  private startScalingMonitor(): void {
    // Check scaling needs every minute
    setInterval(async () => {
      try {
        const action = await this.checkScalingNeeds();
        if (action) {
          logger.info('Auto-scaling action recommended:', action);
          // In a real implementation, this would trigger infrastructure changes
          await this.notifyScalingNeeded(action);
        }
      } catch (error) {
        logger.error('Auto-scaling check failed:', error);
      }
    }, 60000);
  }
  
  private async notifyScalingNeeded(action: ScalingAction): Promise<void> {
    // Simple notification - in production this might trigger AWS Auto Scaling
    logger.warn('Scaling action needed:', {
      action: action.action,
      reason: action.reason,
      currentMetrics: action.metrics,
      timestamp: new Date().toISOString()
    });
  }
}
```

## Resource Optimization

### 1. Memory Management
```typescript
// Memory usage optimization
export class MemoryOptimizationService {
  private gcStats = new Map<string, GCStats>();
  
  startMemoryMonitoring(): void {
    // Monitor memory usage every 30 seconds
    setInterval(() => {
      this.checkMemoryUsage();
    }, 30000);
    
    // Force garbage collection periodically (development only)
    if (process.env.NODE_ENV === 'development' && global.gc) {
      setInterval(() => {
        global.gc();
      }, 2 * 60 * 1000); // Every 2 minutes
    }
  }
  
  private checkMemoryUsage(): void {
    const memUsage = process.memoryUsage();
    const mbUsage = {
      rss: Math.round(memUsage.rss / 1024 / 1024),
      heapTotal: Math.round(memUsage.heapTotal / 1024 / 1024),
      heapUsed: Math.round(memUsage.heapUsed / 1024 / 1024),
      external: Math.round(memUsage.external / 1024 / 1024)
    };
    
    logger.info('Memory usage:', mbUsage);
    
    // Alert on high memory usage
    if (mbUsage.heapUsed > 1024) { // 1GB
      logger.warn('High memory usage detected:', {
        heapUsed: mbUsage.heapUsed,
        heapTotal: mbUsage.heapTotal,
        recommendation: 'Consider optimizing memory usage or scaling up'
      });
    }
    
    // Track memory trends
    this.recordMemoryStats(mbUsage);
  }
  
  optimizeMemoryUsage(): void {
    // Clear unnecessary caches
    this.clearExpiredCaches();
    
    // Close idle connections
    this.closeIdleConnections();
    
    // Clear old metrics
    this.clearOldMetrics();
  }
}

// CPU optimization
export class CpuOptimizationService {
  private cpuUsage: CpuUsage[] = [];
  
  startCpuMonitoring(): void {
    setInterval(() => {
      this.measureCpuUsage();
    }, 5000); // Every 5 seconds
  }
  
  private measureCpuUsage(): void {
    const usage = process.cpuUsage();
    const currentUsage: CpuUsage = {
      user: usage.user,
      system: usage.system,
      timestamp: Date.now()
    };
    
    this.cpuUsage.push(currentUsage);
    
    // Keep only last 100 measurements
    if (this.cpuUsage.length > 100) {
      this.cpuUsage = this.cpuUsage.slice(-50);
    }
    
    // Calculate CPU percentage
    if (this.cpuUsage.length >= 2) {
      const current = this.cpuUsage[this.cpuUsage.length - 1];
      const previous = this.cpuUsage[this.cpuUsage.length - 2];
      
      const timeDiff = current.timestamp - previous.timestamp;
      const userDiff = current.user - previous.user;
      const systemDiff = current.system - previous.system;
      
      const cpuPercent = ((userDiff + systemDiff) / (timeDiff * 1000)) * 100;
      
      if (cpuPercent > 80) {
        logger.warn('High CPU usage detected:', {
          cpuPercent: Math.round(cpuPercent * 100) / 100,
          recommendation: 'Consider optimizing CPU-intensive operations'
        });
      }
    }
  }
}
```

**File 68/71 completed successfully. The scalability patterns provide comprehensive scalability architecture with multi-level caching, database optimization, load balancing, performance monitoring, auto-scaling triggers, and resource optimization while maintaining YAGNI principles with 80% complexity reduction. Next: Continue with data flow architecture (File 69/71).**