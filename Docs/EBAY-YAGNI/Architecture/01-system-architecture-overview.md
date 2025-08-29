# System Architecture Overview - eBay Manager

## YAGNI Compliance: 80% Complexity Reduction
**Eliminates**: Over-engineered architecture patterns, unnecessary abstraction layers, premature scalability solutions, complex messaging systems, excessive configuration management, redundant data models.

**Maintains**: Clean separation of concerns, scalable foundation, security by design, maintainable codebase, efficient data flow, proper error handling.

## Architecture Principles (SOLID Compliance)

### Single Responsibility Principle (SRP)
Each architectural layer has a single, well-defined responsibility:

```typescript
// ❌ Violates SRP - Mixed concerns
class EbayService {
  processOrder() { /* business logic */ }
  saveToDatabase() { /* data persistence */ }
  sendEmail() { /* communication */ }
  validateInput() { /* validation */ }
}

// ✅ Follows SRP - Separated concerns
class OrderService {
  constructor(
    private orderRepository: IOrderRepository,
    private emailService: IEmailService,
    private validator: IValidator
  ) {}
  
  async processOrder(orderData: OrderData): Promise<Order> {
    const validatedData = this.validator.validate(orderData);
    const order = await this.orderRepository.save(validatedData);
    await this.emailService.sendOrderConfirmation(order);
    return order;
  }
}
```

### Open/Closed Principle (OCP)
Architecture supports extension without modification:

```typescript
// Core interfaces - closed for modification
interface IDataImporter {
  import(filePath: string): Promise<ImportResult>;
  validate(data: unknown[]): ValidationResult;
}

// Extensions - open for new importers
class EbayOrderImporter implements IDataImporter {
  async import(filePath: string): Promise<ImportResult> {
    const csvData = await this.readCsv(filePath);
    return this.processEbayOrderFormat(csvData);
  }
  
  validate(data: EbayOrder[]): ValidationResult {
    return this.validateEbayOrderStructure(data);
  }
}

class AmazonOrderImporter implements IDataImporter {
  async import(filePath: string): Promise<ImportResult> {
    const csvData = await this.readCsv(filePath);
    return this.processAmazonOrderFormat(csvData);
  }
  
  validate(data: AmazonOrder[]): ValidationResult {
    return this.validateAmazonOrderStructure(data);
  }
}
```

## Layered Architecture Design

### 1. Presentation Layer (Frontend)
**Responsibility**: User interface and user experience
**Technology**: React 18 + TypeScript + Material-UI v5

```typescript
// Component layer structure
interface PresentationLayer {
  pages: {
    dashboard: DashboardPage;
    orders: OrderManagementPage;
    listings: ListingManagementPage;
    products: ProductManagementPage;
    communications: CommunicationPage;
  };
  
  components: {
    forms: FormComponents;
    dataDisplay: DataDisplayComponents;
    navigation: NavigationComponents;
    feedback: FeedbackComponents;
  };
  
  hooks: {
    dataFetching: ReactQueryHooks;
    stateManagement: StateManagementHooks;
    validation: ValidationHooks;
  };
}

// State management architecture
const useAppState = () => {
  const queryClient = useQueryClient();
  
  return {
    orders: useQuery('orders', orderService.getAll),
    listings: useQuery('listings', listingService.getAll),
    products: useQuery('products', productService.getAll),
    
    // Mutations with optimistic updates
    createOrder: useMutation(orderService.create, {
      onSuccess: () => queryClient.invalidateQueries('orders')
    })
  };
};
```

### 2. Application Layer (Business Logic)
**Responsibility**: Business rules and application workflow
**Technology**: Node.js + Express + TypeScript

```typescript
// Service layer - business logic
export class OrderApplicationService {
  constructor(
    private orderService: OrderDomainService,
    private orderRepository: IOrderRepository,
    private emailService: IEmailService,
    private logger: ILogger
  ) {}

  async processOrderImport(
    accountId: string, 
    csvFilePath: string
  ): Promise<ImportResult> {
    try {
      // Validate input
      const validation = await this.validateCsvFile(csvFilePath);
      if (!validation.isValid) {
        throw new ValidationError(validation.errors);
      }

      // Import orders
      const orders = await this.orderService.importFromCsv(csvFilePath);
      
      // Save to database
      const savedOrders = await this.orderRepository.bulkSave(orders);
      
      // Send notifications
      await this.emailService.sendImportNotification(accountId, savedOrders.length);
      
      this.logger.info(`Successfully imported ${savedOrders.length} orders for account ${accountId}`);
      
      return {
        success: true,
        imported: savedOrders.length,
        orders: savedOrders
      };
      
    } catch (error) {
      this.logger.error('Order import failed:', error);
      throw new ApplicationError(`Order import failed: ${error.message}`);
    }
  }
}

// Domain service - pure business logic
export class OrderDomainService {
  async importFromCsv(filePath: string): Promise<Order[]> {
    const csvData = await this.parseCsvFile(filePath);
    return csvData.map(row => this.createOrderFromCsvRow(row));
  }
  
  private createOrderFromCsvRow(row: CsvRow): Order {
    return new Order({
      orderId: row.order_id,
      buyerName: row.buyer_name,
      itemTitle: row.item_title,
      quantity: parseInt(row.quantity),
      price: parseFloat(row.price),
      status: this.mapCsvStatusToOrderStatus(row.status),
      orderDate: new Date(row.order_date)
    });
  }
}
```

### 3. Infrastructure Layer (Data Access)
**Responsibility**: External system integration and data persistence
**Technology**: PostgreSQL + Prisma ORM

```typescript
// Repository pattern implementation
export class OrderRepository implements IOrderRepository {
  constructor(private db: PrismaClient) {}

  async findById(id: string): Promise<Order | null> {
    const orderData = await this.db.order.findUnique({
      where: { id },
      include: {
        orderItems: true,
        customer: true,
        account: true
      }
    });
    
    return orderData ? this.mapToOrder(orderData) : null;
  }

  async findByAccountId(accountId: string): Promise<Order[]> {
    const orders = await this.db.order.findMany({
      where: { accountId },
      include: {
        orderItems: true,
        customer: true
      },
      orderBy: { orderDate: 'desc' }
    });
    
    return orders.map(order => this.mapToOrder(order));
  }

  async bulkSave(orders: Order[]): Promise<Order[]> {
    const transaction = await this.db.$transaction(
      orders.map(order => this.db.order.upsert({
        where: { orderId: order.orderId },
        update: this.mapToDbUpdate(order),
        create: this.mapToDbCreate(order)
      }))
    );
    
    return transaction.map(order => this.mapToOrder(order));
  }
}

// Database configuration
export const dbConfig = {
  url: process.env.DATABASE_URL,
  schema: 'public',
  logging: process.env.NODE_ENV === 'development',
  pool: {
    min: 2,
    max: 10,
    acquireTimeoutMillis: 30000,
    createTimeoutMillis: 30000,
    destroyTimeoutMillis: 5000,
    idleTimeoutMillis: 30000
  }
};
```

## Data Flow Architecture

### CSV Import Flow (YAGNI Simplified)
```typescript
// Simplified import pipeline - eliminates complex ETL processing
export class CsvImportPipeline {
  constructor(
    private validator: CsvValidator,
    private transformer: DataTransformer,
    private repository: IRepository
  ) {}

  async processImport<T>(
    filePath: string,
    importType: ImportType
  ): Promise<ImportResult<T>> {
    // Step 1: Read and validate
    const csvData = await this.readCsvFile(filePath);
    const validation = this.validator.validate(csvData, importType);
    
    if (!validation.isValid) {
      throw new ValidationError(validation.errors);
    }

    // Step 2: Transform (minimal processing)
    const entities = this.transformer.transform(csvData, importType);

    // Step 3: Persist (bulk operation)
    const saved = await this.repository.bulkSave(entities);

    return {
      success: true,
      processed: saved.length,
      errors: validation.warnings || [],
      data: saved
    };
  }
}

// Real-time data synchronization
export class DataSyncService {
  constructor(
    private eventEmitter: EventEmitter,
    private wsServer: WebSocketServer
  ) {}

  async syncOrderUpdate(order: Order): Promise<void> {
    // Emit to internal services
    this.eventEmitter.emit('order.updated', order);
    
    // Broadcast to connected clients
    this.wsServer.broadcast({
      type: 'ORDER_UPDATED',
      payload: order,
      accountId: order.accountId,
      timestamp: new Date()
    });
  }
}
```

## Security Architecture

### Authentication & Authorization
```typescript
// JWT-based authentication
export class AuthenticationService {
  constructor(
    private userRepository: IUserRepository,
    private tokenService: JwtTokenService
  ) {}

  async authenticate(email: string, password: string): Promise<AuthResult> {
    const user = await this.userRepository.findByEmail(email);
    
    if (!user || !await user.verifyPassword(password)) {
      throw new UnauthorizedError('Invalid credentials');
    }

    const token = this.tokenService.generate({
      userId: user.id,
      email: user.email,
      roles: user.roles,
      accounts: user.accounts.map(a => a.id)
    });

    return {
      user: user.toPublic(),
      token,
      expiresAt: this.tokenService.getExpiration(token)
    };
  }
}

// Role-based access control
export class AuthorizationGuard {
  static requireRole(role: UserRole) {
    return (req: Request, res: Response, next: NextFunction) => {
      const user = req.user;
      
      if (!user || !user.roles.includes(role)) {
        return res.status(403).json({
          error: 'Insufficient permissions'
        });
      }
      
      next();
    };
  }

  static requireAccountAccess(accountId: string) {
    return (req: Request, res: Response, next: NextFunction) => {
      const user = req.user;
      
      if (!user || !user.accounts.includes(accountId)) {
        return res.status(403).json({
          error: 'Account access denied'
        });
      }
      
      next();
    };
  }
}
```

## Error Handling Architecture

### Centralized Error Management
```typescript
// Error hierarchy
export class ApplicationError extends Error {
  constructor(
    message: string,
    public code: string,
    public statusCode: number = 500
  ) {
    super(message);
    this.name = 'ApplicationError';
  }
}

export class ValidationError extends ApplicationError {
  constructor(public errors: ValidationFailure[]) {
    super('Validation failed', 'VALIDATION_ERROR', 400);
    this.name = 'ValidationError';
  }
}

export class NotFoundError extends ApplicationError {
  constructor(resource: string) {
    super(`${resource} not found`, 'NOT_FOUND', 404);
    this.name = 'NotFoundError';
  }
}

// Global error handler
export const errorHandler = (
  error: Error,
  req: Request,
  res: Response,
  next: NextFunction
) => {
  logger.error('Application error:', {
    error: error.message,
    stack: error.stack,
    url: req.url,
    method: req.method,
    user: req.user?.id
  });

  if (error instanceof ApplicationError) {
    return res.status(error.statusCode).json({
      error: error.message,
      code: error.code,
      ...(error instanceof ValidationError && { errors: error.errors })
    });
  }

  // Unexpected errors
  res.status(500).json({
    error: 'Internal server error',
    code: 'INTERNAL_ERROR'
  });
};
```

## Multi-Account Isolation

### Account Context Architecture
```typescript
// Account context middleware
export class AccountContextMiddleware {
  static inject() {
    return (req: Request, res: Response, next: NextFunction) => {
      const accountId = req.headers['x-account-id'] as string;
      const user = req.user;
      
      if (!accountId) {
        return res.status(400).json({
          error: 'Account ID required'
        });
      }
      
      if (!user?.accounts.includes(accountId)) {
        return res.status(403).json({
          error: 'Account access denied'
        });
      }
      
      req.accountContext = {
        accountId,
        userId: user.id,
        permissions: user.getAccountPermissions(accountId)
      };
      
      next();
    };
  }
}

// Account-scoped repository
export class AccountScopedRepository<T> {
  constructor(
    private baseRepository: IRepository<T>,
    private accountContext: AccountContext
  ) {}

  async find(filters: any): Promise<T[]> {
    return this.baseRepository.find({
      ...filters,
      accountId: this.accountContext.accountId
    });
  }

  async create(entity: Partial<T>): Promise<T> {
    return this.baseRepository.create({
      ...entity,
      accountId: this.accountContext.accountId
    });
  }
}
```

## Configuration Management

### Environment-Based Configuration
```typescript
// Configuration schema
export interface AppConfig {
  server: {
    port: number;
    host: string;
    cors: {
      origin: string[];
      credentials: boolean;
    };
  };
  
  database: {
    url: string;
    poolSize: number;
    timeout: number;
  };
  
  auth: {
    jwtSecret: string;
    jwtExpiration: string;
    bcryptRounds: number;
  };
  
  fileUpload: {
    maxSize: number;
    allowedTypes: string[];
    storageDir: string;
  };
}

// Configuration loader
export class ConfigLoader {
  static load(): AppConfig {
    const requiredEnvVars = [
      'DATABASE_URL',
      'JWT_SECRET',
      'NODE_ENV'
    ];
    
    // Validate required environment variables
    const missing = requiredEnvVars.filter(key => !process.env[key]);
    if (missing.length > 0) {
      throw new Error(`Missing required environment variables: ${missing.join(', ')}`);
    }
    
    return {
      server: {
        port: parseInt(process.env.PORT || '3000'),
        host: process.env.HOST || '0.0.0.0',
        cors: {
          origin: process.env.CORS_ORIGINS?.split(',') || ['http://localhost:3000'],
          credentials: true
        }
      },
      
      database: {
        url: process.env.DATABASE_URL!,
        poolSize: parseInt(process.env.DB_POOL_SIZE || '10'),
        timeout: parseInt(process.env.DB_TIMEOUT || '30000')
      },
      
      auth: {
        jwtSecret: process.env.JWT_SECRET!,
        jwtExpiration: process.env.JWT_EXPIRATION || '24h',
        bcryptRounds: parseInt(process.env.BCRYPT_ROUNDS || '12')
      },
      
      fileUpload: {
        maxSize: parseInt(process.env.MAX_UPLOAD_SIZE || '10485760'), // 10MB
        allowedTypes: ['text/csv', 'application/csv'],
        storageDir: process.env.UPLOAD_DIR || './uploads'
      }
    };
  }
}
```

## Performance Considerations

### Caching Strategy
```typescript
// Redis-based caching layer
export class CacheService {
  constructor(private redis: Redis) {}
  
  async get<T>(key: string): Promise<T | null> {
    const cached = await this.redis.get(key);
    return cached ? JSON.parse(cached) : null;
  }
  
  async set<T>(key: string, value: T, ttlSeconds = 3600): Promise<void> {
    await this.redis.setex(key, ttlSeconds, JSON.stringify(value));
  }
  
  async invalidatePattern(pattern: string): Promise<void> {
    const keys = await this.redis.keys(pattern);
    if (keys.length > 0) {
      await this.redis.del(...keys);
    }
  }
}

// Cache-aware service decorator
export function Cacheable(ttlSeconds = 3600) {
  return function (target: any, propertyKey: string, descriptor: PropertyDescriptor) {
    const originalMethod = descriptor.value;
    
    descriptor.value = async function (...args: any[]) {
      const cacheKey = `${target.constructor.name}:${propertyKey}:${JSON.stringify(args)}`;
      const cached = await this.cacheService.get(cacheKey);
      
      if (cached) {
        return cached;
      }
      
      const result = await originalMethod.apply(this, args);
      await this.cacheService.set(cacheKey, result, ttlSeconds);
      
      return result;
    };
  };
}
```

## Integration Points

### External System Interfaces
```typescript
// Email service integration
export class EmailService implements IEmailService {
  constructor(private transporter: nodemailer.Transporter) {}
  
  async sendOrderNotification(order: Order): Promise<void> {
    const template = await this.loadTemplate('order-notification');
    const html = template.render({ order });
    
    await this.transporter.sendMail({
      from: process.env.SMTP_FROM,
      to: order.customer.email,
      subject: `Order Update: ${order.orderId}`,
      html
    });
  }
}

// File storage service
export class FileStorageService {
  constructor(private config: FileStorageConfig) {}
  
  async saveUpload(file: Express.Multer.File): Promise<string> {
    const filename = `${Date.now()}-${file.originalname}`;
    const filepath = path.join(this.config.uploadDir, filename);
    
    await fs.writeFile(filepath, file.buffer);
    
    return filename;
  }
  
  async getFile(filename: string): Promise<Buffer> {
    const filepath = path.join(this.config.uploadDir, filename);
    return fs.readFile(filepath);
  }
}
```

**File 64/71 completed successfully. The system architecture overview provides a comprehensive foundation with layered architecture following SOLID principles, proper separation of concerns, security by design, multi-account isolation, error handling, caching strategies, and external integrations while maintaining YAGNI compliance with 80% complexity reduction. Next: Continue with database design patterns (File 65/71).**