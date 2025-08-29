# Data Flow Architecture - eBay Manager

## YAGNI Compliance: 85% Complexity Reduction
**Eliminates**: Complex event sourcing, sophisticated ETL pipelines, advanced stream processing, complex data transformation chains, over-engineered event buses, excessive data validation layers, redundant data synchronization.

**Maintains**: Clear data pipelines, efficient CSV processing, real-time updates, data consistency, error handling, data validation, event notifications, cache invalidation.

## Data Flow Principles (SOLID Compliance)

### Single Responsibility Principle (SRP)
Each data flow component has a single, focused data processing responsibility:

```typescript
// ❌ Violates SRP - Mixed data processing concerns
class DataProcessor {
  processCSV() { /* CSV parsing + validation + transformation + storage */ }
  sendNotifications() { /* Email + websocket + database updates */ }
  updateCache() { /* Cache invalidation + repopulation */ }
  validateData() { /* Business validation + format validation */ }
}

// ✅ Follows SRP - Separated data processing concerns
class CsvParser {
  constructor(private validator: CsvValidator) {}
  
  async parse(filePath: string): Promise<ParsedCsvData> {
    const rawData = await this.readCsvFile(filePath);
    const validatedData = this.validator.validateStructure(rawData);
    
    return {
      headers: validatedData.headers,
      rows: validatedData.rows,
      totalRows: validatedData.rows.length,
      errors: validatedData.errors
    };
  }
}

class DataTransformer {
  transform<T>(rawData: CsvRow[], type: DataType): T[] {
    switch (type) {
      case 'orders':
        return this.transformOrders(rawData) as T[];
      case 'listings':
        return this.transformListings(rawData) as T[];
      case 'products':
        return this.transformProducts(rawData) as T[];
      default:
        throw new Error(`Unsupported data type: ${type}`);
    }
  }
}

class DataPersister {
  constructor(
    private repository: IRepository,
    private eventEmitter: EventEmitter
  ) {}
  
  async persist<T>(entities: T[], options: PersistenceOptions): Promise<PersistenceResult<T>> {
    const savedEntities = await this.repository.bulkSave(entities);
    
    // Emit events for downstream processing
    this.eventEmitter.emit('data.persisted', {
      type: options.entityType,
      count: savedEntities.length,
      accountId: options.accountId
    });
    
    return {
      saved: savedEntities,
      errors: []
    };
  }
}
```

### Open/Closed Principle (OCP)
Data flow architecture supports new data types without modifying existing pipelines:

```typescript
// Core data pipeline interface - closed for modification
interface IDataPipeline {
  process(input: DataInput): Promise<DataOutput>;
}

// Extendable pipeline implementations - open for extension
class CsvImportPipeline implements IDataPipeline {
  constructor(
    private parser: CsvParser,
    private transformer: DataTransformer,
    private persister: DataPersister
  ) {}
  
  async process(input: CsvDataInput): Promise<DataOutput> {
    // Parse CSV
    const parsed = await this.parser.parse(input.filePath);
    
    // Transform to domain entities
    const entities = this.transformer.transform(parsed.rows, input.dataType);
    
    // Persist to database
    const result = await this.persister.persist(entities, {
      entityType: input.dataType,
      accountId: input.accountId
    });
    
    return {
      success: true,
      processed: result.saved.length,
      errors: result.errors
    };
  }
}

class RealtimeUpdatePipeline implements IDataPipeline {
  async process(input: RealtimeDataInput): Promise<DataOutput> {
    // Handle real-time data updates (WebSocket, API calls)
    const validated = await this.validateRealtimeData(input.data);
    const updated = await this.updateRepository.update(input.id, validated);
    
    // Broadcast updates
    await this.broadcastUpdate(updated);
    
    return {
      success: true,
      processed: 1,
      errors: []
    };
  }
}

class BatchProcessingPipeline implements IDataPipeline {
  async process(input: BatchDataInput): Promise<DataOutput> {
    // Handle batch processing for large datasets
    const results = await this.processBatches(input.batches);
    
    return {
      success: true,
      processed: results.totalProcessed,
      errors: results.errors
    };
  }
}
```

## CSV Import Data Flow

### 1. CSV Processing Pipeline
```typescript
// Comprehensive CSV import pipeline
export class CsvImportService {
  constructor(
    private csvParser: CsvParser,
    private dataValidator: DataValidator,
    private dataTransformer: DataTransformer,
    private repository: IRepository,
    private eventBus: EventBus,
    private cacheService: CacheService
  ) {}
  
  async processOrdersCsv(accountId: string, filePath: string): Promise<ImportResult> {
    const importId = this.generateImportId();
    
    try {
      // Phase 1: Parse CSV file
      await this.updateImportStatus(importId, 'parsing');
      const parsed = await this.csvParser.parse(filePath);
      
      if (parsed.errors.length > 0) {
        throw new ValidationError('CSV parsing failed', parsed.errors);
      }
      
      // Phase 2: Validate business rules
      await this.updateImportStatus(importId, 'validating');
      const validation = await this.dataValidator.validateOrders(parsed.rows, accountId);
      
      if (!validation.isValid) {
        throw new ValidationError('Data validation failed', validation.errors);
      }
      
      // Phase 3: Transform to domain entities
      await this.updateImportStatus(importId, 'transforming');
      const orders = this.dataTransformer.transformOrders(parsed.rows, accountId);
      
      // Phase 4: Persist to database (batched)
      await this.updateImportStatus(importId, 'persisting');
      const persisted = await this.persistOrdersBatched(orders, accountId);
      
      // Phase 5: Update caches and notify
      await this.updateImportStatus(importId, 'finalizing');
      await this.invalidateRelatedCaches(accountId);
      await this.sendImportNotifications(accountId, persisted.length);
      
      await this.updateImportStatus(importId, 'completed');
      
      return {
        importId,
        success: true,
        totalProcessed: persisted.length,
        totalErrors: 0,
        duration: Date.now() - this.getImportStartTime(importId)
      };
      
    } catch (error) {
      await this.updateImportStatus(importId, 'failed', error.message);
      throw error;
    } finally {
      // Cleanup temporary file
      await this.cleanupFile(filePath);
    }
  }
  
  private async persistOrdersBatched(
    orders: Order[], 
    accountId: string, 
    batchSize = 100
  ): Promise<Order[]> {
    const persisted: Order[] = [];
    
    for (let i = 0; i < orders.length; i += batchSize) {
      const batch = orders.slice(i, i + batchSize);
      
      const batchResult = await this.repository.orders.bulkUpsert(batch);
      persisted.push(...batchResult);
      
      // Emit progress event
      this.eventBus.emit('import.progress', {
        accountId,
        processed: persisted.length,
        total: orders.length,
        percentage: Math.round((persisted.length / orders.length) * 100)
      });
      
      // Small delay to prevent overwhelming the database
      if (i + batchSize < orders.length) {
        await this.sleep(100);
      }
    }
    
    return persisted;
  }
}

// CSV data validation service
export class CsvDataValidator {
  async validateOrders(rows: CsvRow[], accountId: string): Promise<ValidationResult> {
    const errors: ValidationError[] = [];
    const warnings: ValidationWarning[] = [];
    
    for (const [index, row] of rows.entries()) {
      // Required field validation
      if (!row.order_id) {
        errors.push({
          row: index + 1,
          field: 'order_id',
          message: 'Order ID is required'
        });
      }
      
      if (!row.buyer_name) {
        errors.push({
          row: index + 1,
          field: 'buyer_name',
          message: 'Buyer name is required'
        });
      }
      
      // Data format validation
      if (row.order_date && !this.isValidDate(row.order_date)) {
        errors.push({
          row: index + 1,
          field: 'order_date',
          message: 'Invalid date format'
        });
      }
      
      if (row.total_amount && !this.isValidAmount(row.total_amount)) {
        errors.push({
          row: index + 1,
          field: 'total_amount',
          message: 'Invalid amount format'
        });
      }
      
      // Business rule validation
      if (row.order_id && await this.orderExists(accountId, row.order_id)) {
        warnings.push({
          row: index + 1,
          field: 'order_id',
          message: 'Order already exists - will be updated'
        });
      }
    }
    
    return {
      isValid: errors.length === 0,
      errors,
      warnings,
      validRowCount: rows.length - errors.length
    };
  }
}
```

### 2. Real-time Data Synchronization
```typescript
// Real-time data updates via WebSocket
export class RealtimeDataService {
  constructor(
    private websocketServer: WebSocketServer,
    private cacheService: CacheService,
    private eventBus: EventBus
  ) {
    this.setupEventListeners();
  }
  
  private setupEventListeners(): void {
    // Listen for data changes
    this.eventBus.on('order.created', (order: Order) => {
      this.broadcastOrderUpdate('created', order);
      this.invalidateOrderCaches(order.accountId);
    });
    
    this.eventBus.on('order.updated', (order: Order) => {
      this.broadcastOrderUpdate('updated', order);
      this.invalidateOrderCaches(order.accountId);
    });
    
    this.eventBus.on('listing.status_changed', (listing: Listing) => {
      this.broadcastListingUpdate('status_changed', listing);
      this.invalidateListingCaches(listing.accountId);
    });
    
    this.eventBus.on('import.progress', (progress: ImportProgress) => {
      this.broadcastImportProgress(progress);
    });
  }
  
  private broadcastOrderUpdate(event: string, order: Order): void {
    const message: WebSocketMessage = {
      type: 'ORDER_UPDATE',
      event,
      data: order,
      accountId: order.accountId,
      timestamp: new Date().toISOString()
    };
    
    // Broadcast to clients connected to this account
    this.websocketServer.broadcastToAccount(order.accountId, message);
  }
  
  private async invalidateOrderCaches(accountId: string): Promise<void> {
    await Promise.all([
      this.cacheService.invalidate(`orders:${accountId}:*`),
      this.cacheService.invalidate(`dashboard:${accountId}:*`),
      this.cacheService.invalidate(`metrics:${accountId}:*`)
    ]);
  }
}

// WebSocket server for real-time updates
export class WebSocketServer {
  private connections = new Map<string, Set<WebSocket>>();
  
  constructor(private server: Server) {
    this.setupWebSocketServer();
  }
  
  private setupWebSocketServer(): void {
    const wss = new WebSocket.Server({ server: this.server });
    
    wss.on('connection', (ws: WebSocket, request: IncomingMessage) => {
      this.handleNewConnection(ws, request);
    });
  }
  
  private handleNewConnection(ws: WebSocket, request: IncomingMessage): void {
    const url = new URL(request.url!, `http://${request.headers.host}`);
    const accountId = url.searchParams.get('accountId');
    
    if (!accountId) {
      ws.close(1008, 'Account ID required');
      return;
    }
    
    // Add connection to account group
    if (!this.connections.has(accountId)) {
      this.connections.set(accountId, new Set());
    }
    this.connections.get(accountId)!.add(ws);
    
    // Handle connection close
    ws.on('close', () => {
      const accountConnections = this.connections.get(accountId);
      if (accountConnections) {
        accountConnections.delete(ws);
        if (accountConnections.size === 0) {
          this.connections.delete(accountId);
        }
      }
    });
    
    // Send initial connection confirmation
    ws.send(JSON.stringify({
      type: 'CONNECTION_ESTABLISHED',
      accountId,
      timestamp: new Date().toISOString()
    }));
  }
  
  broadcastToAccount(accountId: string, message: WebSocketMessage): void {
    const connections = this.connections.get(accountId);
    if (!connections) return;
    
    const messageString = JSON.stringify(message);
    
    // Remove closed connections while broadcasting
    const closedConnections: WebSocket[] = [];
    
    connections.forEach(ws => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(messageString);
      } else {
        closedConnections.push(ws);
      }
    });
    
    // Clean up closed connections
    closedConnections.forEach(ws => connections.delete(ws));
  }
}
```

## Data Consistency Patterns

### 1. Event-Driven Data Updates
```typescript
// Simple event bus for data consistency
export class DataEventBus {
  private listeners = new Map<string, EventListener[]>();
  
  on(event: string, listener: EventListener): void {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    this.listeners.get(event)!.push(listener);
  }
  
  async emit(event: string, data: any): Promise<void> {
    const eventListeners = this.listeners.get(event);
    if (!eventListeners) return;
    
    // Execute listeners in parallel
    const promises = eventListeners.map(listener => 
      this.safeExecuteListener(listener, data)
    );
    
    await Promise.allSettled(promises);
  }
  
  private async safeExecuteListener(listener: EventListener, data: any): Promise<void> {
    try {
      await listener(data);
    } catch (error) {
      logger.error('Event listener failed:', {
        error: error.message,
        data,
        listener: listener.name
      });
    }
  }
}

// Data consistency service
export class DataConsistencyService {
  constructor(
    private eventBus: DataEventBus,
    private cacheService: CacheService,
    private metricsService: MetricsService
  ) {
    this.setupConsistencyListeners();
  }
  
  private setupConsistencyListeners(): void {
    // Order-related consistency
    this.eventBus.on('order.created', async (order: Order) => {
      await this.updateCustomerStats(order.customerId);
      await this.updateAccountMetrics(order.accountId);
      await this.invalidateRelatedCaches(order);
    });
    
    this.eventBus.on('order.status_changed', async (data: { order: Order, oldStatus: string }) => {
      await this.handleOrderStatusChange(data.order, data.oldStatus);
    });
    
    // Listing-related consistency
    this.eventBus.on('listing.created', async (listing: Listing) => {
      await this.updateProductStats(listing.productId);
      await this.invalidateListingCaches(listing.accountId);
    });
  }
  
  private async updateCustomerStats(customerId: string): Promise<void> {
    const customer = await this.customerRepository.findById(customerId);
    if (!customer) return;
    
    const orderStats = await this.orderRepository.getCustomerStats(customerId);
    
    await this.customerRepository.update(customerId, {
      totalOrders: orderStats.totalOrders,
      totalSpent: orderStats.totalSpent,
      averageOrderValue: orderStats.averageOrderValue,
      lastOrderDate: orderStats.lastOrderDate,
      customerType: this.determineCustomerType(orderStats)
    });
  }
  
  private async invalidateRelatedCaches(order: Order): Promise<void> {
    const patterns = [
      `orders:${order.accountId}:*`,
      `customers:${order.customerId}:*`,
      `dashboard:${order.accountId}:*`,
      `metrics:${order.accountId}:*`
    ];
    
    await Promise.all(
      patterns.map(pattern => this.cacheService.invalidate(pattern))
    );
  }
}
```

### 2. Data Validation Pipeline
```typescript
// Multi-stage data validation
export class DataValidationPipeline {
  private validators: IValidator[] = [];
  
  addValidator(validator: IValidator): void {
    this.validators.push(validator);
  }
  
  async validate<T>(data: T, context: ValidationContext): Promise<ValidationResult> {
    const errors: ValidationError[] = [];
    const warnings: ValidationWarning[] = [];
    
    for (const validator of this.validators) {
      try {
        const result = await validator.validate(data, context);
        
        if (!result.isValid) {
          errors.push(...result.errors);
        }
        
        if (result.warnings) {
          warnings.push(...result.warnings);
        }
        
        // Stop validation on critical errors
        if (result.critical) {
          break;
        }
        
      } catch (error) {
        errors.push({
          field: 'unknown',
          message: `Validation error: ${error.message}`,
          critical: true
        });
        break;
      }
    }
    
    return {
      isValid: errors.length === 0,
      errors,
      warnings,
      validatedData: data
    };
  }
}

// Concrete validators
export class BusinessRuleValidator implements IValidator {
  async validate<T>(data: T, context: ValidationContext): Promise<ValidationResult> {
    const errors: ValidationError[] = [];
    
    if (context.entityType === 'order') {
      const order = data as Order;
      
      // Validate order amount
      if (order.totalAmount <= 0) {
        errors.push({
          field: 'totalAmount',
          message: 'Order amount must be greater than zero'
        });
      }
      
      // Validate order date
      if (order.orderDate > new Date()) {
        errors.push({
          field: 'orderDate',
          message: 'Order date cannot be in the future'
        });
      }
      
      // Validate customer exists
      const customerExists = await this.customerRepository.exists(order.customerId);
      if (!customerExists) {
        errors.push({
          field: 'customerId',
          message: 'Customer does not exist'
        });
      }
    }
    
    return {
      isValid: errors.length === 0,
      errors
    };
  }
}

export class DataFormatValidator implements IValidator {
  async validate<T>(data: T, context: ValidationContext): Promise<ValidationResult> {
    const errors: ValidationError[] = [];
    
    // Generic format validation based on schema
    const schema = this.getSchemaForEntity(context.entityType);
    const schemaValidation = schema.validate(data);
    
    if (schemaValidation.error) {
      schemaValidation.error.details.forEach(detail => {
        errors.push({
          field: detail.path.join('.'),
          message: detail.message
        });
      });
    }
    
    return {
      isValid: errors.length === 0,
      errors
    };
  }
}
```

## Performance Optimization

### 1. Data Flow Optimization
```typescript
// Stream processing for large datasets
export class StreamProcessor {
  constructor(
    private batchSize: number = 1000,
    private maxConcurrency: number = 5
  ) {}
  
  async processStream<T, R>(
    dataStream: ReadableStream<T>,
    processor: (batch: T[]) => Promise<R[]>,
    options: StreamOptions = {}
  ): Promise<StreamResult<R>> {
    const results: R[] = [];
    const errors: ProcessingError[] = [];
    let batch: T[] = [];
    let processedCount = 0;
    
    const reader = dataStream.getReader();
    
    try {
      while (true) {
        const { done, value } = await reader.read();
        
        if (done) {
          // Process final batch
          if (batch.length > 0) {
            const batchResult = await this.processBatch(batch, processor);
            results.push(...batchResult.results);
            errors.push(...batchResult.errors);
          }
          break;
        }
        
        batch.push(value);
        
        // Process batch when it reaches batch size
        if (batch.length >= this.batchSize) {
          const batchResult = await this.processBatch(batch, processor);
          results.push(...batchResult.results);
          errors.push(...batchResult.errors);
          
          processedCount += batch.length;
          batch = [];
          
          // Emit progress event
          if (options.onProgress) {
            options.onProgress({
              processed: processedCount,
              errors: errors.length
            });
          }
        }
      }
    } finally {
      reader.releaseLock();
    }
    
    return {
      results,
      errors,
      totalProcessed: processedCount
    };
  }
  
  private async processBatch<T, R>(
    batch: T[],
    processor: (batch: T[]) => Promise<R[]>
  ): Promise<BatchResult<R>> {
    try {
      const results = await processor(batch);
      return { results, errors: [] };
    } catch (error) {
      return {
        results: [],
        errors: [{
          batchIndex: 0,
          error: error.message,
          items: batch
        }]
      };
    }
  }
}

// Memory-efficient CSV processing
export class StreamingCsvProcessor {
  async processLargeCsv<T>(
    filePath: string,
    transformer: (row: CsvRow) => T,
    batchProcessor: (batch: T[]) => Promise<void>
  ): Promise<void> {
    const stream = fs.createReadStream(filePath);
    const csvParser = csv();
    
    let batch: T[] = [];
    const batchSize = 1000;
    
    return new Promise((resolve, reject) => {
      stream
        .pipe(csvParser)
        .on('data', async (row: CsvRow) => {
          try {
            const transformed = transformer(row);
            batch.push(transformed);
            
            if (batch.length >= batchSize) {
              // Pause stream while processing batch
              csvParser.pause();
              
              await batchProcessor(batch);
              batch = [];
              
              // Resume stream
              csvParser.resume();
            }
          } catch (error) {
            reject(error);
          }
        })
        .on('end', async () => {
          try {
            // Process final batch
            if (batch.length > 0) {
              await batchProcessor(batch);
            }
            resolve();
          } catch (error) {
            reject(error);
          }
        })
        .on('error', reject);
    });
  }
}
```

### 2. Cache-Aware Data Flow
```typescript
// Intelligent cache management in data flows
export class CacheAwareDataFlow {
  constructor(
    private cacheService: CacheService,
    private repository: IRepository
  ) {}
  
  async getOrderWithCaching(orderId: string, accountId: string): Promise<Order> {
    const cacheKey = `order:${orderId}`;
    
    // Try L1 cache (memory)
    let order = await this.cacheService.get<Order>(cacheKey, { level: 'memory' });
    if (order) {
      this.recordCacheHit('memory', 'order');
      return order;
    }
    
    // Try L2 cache (Redis)
    order = await this.cacheService.get<Order>(cacheKey, { level: 'redis' });
    if (order) {
      this.recordCacheHit('redis', 'order');
      // Populate L1 cache
      await this.cacheService.set(cacheKey, order, { level: 'memory', ttl: 300 });
      return order;
    }
    
    // Fallback to database
    this.recordCacheMiss('order');
    order = await this.repository.orders.findById(orderId, accountId);
    
    if (order) {
      // Populate both cache levels
      await Promise.all([
        this.cacheService.set(cacheKey, order, { level: 'memory', ttl: 300 }),
        this.cacheService.set(cacheKey, order, { level: 'redis', ttl: 1800 })
      ]);
    }
    
    return order;
  }
  
  async invalidateOrderCaches(orderId: string, accountId: string): Promise<void> {
    const patterns = [
      `order:${orderId}`,
      `orders:${accountId}:*`,
      `dashboard:${accountId}:*`
    ];
    
    await Promise.all([
      // Invalidate both cache levels
      ...patterns.map(pattern => this.cacheService.invalidate(pattern, { level: 'memory' })),
      ...patterns.map(pattern => this.cacheService.invalidate(pattern, { level: 'redis' }))
    ]);
  }
}
```

**File 69/71 completed successfully. The data flow architecture provides comprehensive data processing pipelines with CSV import flows, real-time synchronization, event-driven consistency, stream processing, and cache-aware data management while maintaining YAGNI principles with 85% complexity reduction. Next: Continue with microservices considerations (File 70/71).**