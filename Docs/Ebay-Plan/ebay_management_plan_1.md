# Plan 1: Database Setup & Foundation

## Objective
Create database schema, migrations, and foundational models for eBay management system with multi-account support.

## Tech Stack
- Backend: Node.js + Express + TypeScript
- Database: PostgreSQL with Prisma ORM
- Validation: Zod schemas
- Environment: Docker for development

## Database Schema Implementation

### Core Tables

#### 1. Users Table
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    role VARCHAR(20) DEFAULT 'operator',
    max_accounts_allowed INTEGER DEFAULT 3,
    is_active BOOLEAN DEFAULT true,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
```

#### 2. eBay Accounts Table
```sql
CREATE TABLE ebay_accounts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    account_name VARCHAR(100) NOT NULL,
    account_email VARCHAR(255) NOT NULL,
    ebay_username VARCHAR(100),
    browser_profile_path VARCHAR(500),
    account_status VARCHAR(20) DEFAULT 'active',
    last_sync_at TIMESTAMP,
    sync_frequency INTEGER DEFAULT 240, -- minutes
    notes TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_ebay_accounts_user_id ON ebay_accounts(user_id);
CREATE INDEX idx_ebay_accounts_status ON ebay_accounts(account_status);
```

#### 3. User Account Permissions
```sql
CREATE TABLE user_account_permissions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    account_id INTEGER REFERENCES ebay_accounts(id) ON DELETE CASCADE,
    permission_level VARCHAR(20) DEFAULT 'full',
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    assigned_by INTEGER REFERENCES users(id),
    UNIQUE(user_id, account_id)
);
```

#### 4. Sync History
```sql
CREATE TABLE sync_history (
    id SERIAL PRIMARY KEY,
    account_id INTEGER REFERENCES ebay_accounts(id) ON DELETE CASCADE,
    sync_type VARCHAR(50) NOT NULL,
    file_name VARCHAR(255),
    file_size BIGINT,
    records_processed INTEGER DEFAULT 0,
    records_success INTEGER DEFAULT 0,
    records_failed INTEGER DEFAULT 0,
    sync_status VARCHAR(20) DEFAULT 'pending',
    error_message TEXT,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    processing_time INTEGER -- seconds
);

CREATE INDEX idx_sync_history_account_id ON sync_history(account_id);
CREATE INDEX idx_sync_history_sync_type ON sync_history(sync_type);
```

## File Structure

```
ebay-management/
├── package.json
├── tsconfig.json
├── docker-compose.yml
├── .env.example
├── prisma/
│   ├── schema.prisma
│   └── migrations/
├── src/
│   ├── app.ts
│   ├── server.ts
│   ├── config/
│   │   ├── database.ts
│   │   └── environment.ts
│   ├── models/
│   │   ├── User.ts
│   │   ├── EbayAccount.ts
│   │   └── SyncHistory.ts
│   ├── schemas/
│   │   ├── user.schema.ts
│   │   ├── account.schema.ts
│   │   └── sync.schema.ts
│   ├── utils/
│   │   ├── logger.ts
│   │   ├── validation.ts
│   │   └── database.ts
│   └── types/
│       ├── user.types.ts
│       ├── account.types.ts
│       └── common.types.ts
├── tests/
│   ├── unit/
│   └── integration/
└── docs/
    └── database.md
```

## Implementation Files

### 1. package.json
```json
{
  "name": "ebay-management-system",
  "version": "1.0.0",
  "description": "Multi-account eBay management system with CSV sync",
  "main": "dist/server.js",
  "scripts": {
    "dev": "nodemon src/server.ts",
    "build": "tsc",
    "start": "node dist/server.js",
    "db:generate": "prisma generate",
    "db:migrate": "prisma migrate dev",
    "db:push": "prisma db push",
    "db:studio": "prisma studio",
    "test": "jest",
    "test:watch": "jest --watch",
    "lint": "eslint src/**/*.ts",
    "lint:fix": "eslint src/**/*.ts --fix"
  },
  "dependencies": {
    "@prisma/client": "^5.7.1",
    "express": "^4.18.2",
    "express-rate-limit": "^7.1.5",
    "helmet": "^7.1.0",
    "cors": "^2.8.5",
    "dotenv": "^16.3.1",
    "bcryptjs": "^2.4.3",
    "jsonwebtoken": "^9.0.2",
    "multer": "^1.4.5-lts.1",
    "csv-parser": "^3.0.0",
    "zod": "^3.22.4",
    "winston": "^3.11.0",
    "compression": "^1.7.4"
  },
  "devDependencies": {
    "@types/node": "^20.10.5",
    "@types/express": "^4.17.21",
    "@types/bcryptjs": "^2.4.6",
    "@types/jsonwebtoken": "^9.0.5",
    "@types/multer": "^1.4.11",
    "@types/compression": "^1.7.5",
    "typescript": "^5.3.3",
    "nodemon": "^3.0.2",
    "ts-node": "^10.9.2",
    "prisma": "^5.7.1",
    "@typescript-eslint/eslint-plugin": "^6.15.0",
    "@typescript-eslint/parser": "^6.15.0",
    "eslint": "^8.56.0",
    "jest": "^29.7.0",
    "@types/jest": "^29.5.11",
    "ts-jest": "^29.1.1"
  }
}
```

### 2. Prisma Schema
```prisma
// prisma/schema.prisma
generator client {
  provider = "prisma-client-js"
}

datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}

model User {
  id                  Int      @id @default(autoincrement())
  username            String   @unique @db.VarChar(50)
  email               String   @unique @db.VarChar(255)
  passwordHash        String   @map("password_hash") @db.VarChar(255)
  fullName            String?  @map("full_name") @db.VarChar(255)
  role                String   @default("operator") @db.VarChar(20)
  maxAccountsAllowed  Int      @default(3) @map("max_accounts_allowed")
  isActive            Boolean  @default(true) @map("is_active")
  lastLogin           DateTime? @map("last_login")
  createdAt           DateTime @default(now()) @map("created_at")
  updatedAt           DateTime @updatedAt @map("updated_at")

  // Relations
  ebayAccounts        EbayAccount[]
  accountPermissions  UserAccountPermission[]
  assignedPermissions UserAccountPermission[] @relation("AssignedBy")

  @@map("users")
}

model EbayAccount {
  id                 Int      @id @default(autoincrement())
  userId             Int      @map("user_id")
  accountName        String   @map("account_name") @db.VarChar(100)
  accountEmail       String   @map("account_email") @db.VarChar(255)
  ebayUsername       String?  @map("ebay_username") @db.VarChar(100)
  browserProfilePath String?  @map("browser_profile_path") @db.VarChar(500)
  accountStatus      String   @default("active") @map("account_status") @db.VarChar(20)
  lastSyncAt         DateTime? @map("last_sync_at")
  syncFrequency      Int      @default(240) @map("sync_frequency")
  notes              String?
  isActive           Boolean  @default(true) @map("is_active")
  createdAt          DateTime @default(now()) @map("created_at")
  updatedAt          DateTime @updatedAt @map("updated_at")

  // Relations
  user               User     @relation(fields: [userId], references: [id], onDelete: Cascade)
  accountPermissions UserAccountPermission[]
  syncHistory        SyncHistory[]

  @@map("ebay_accounts")
}

model UserAccountPermission {
  id              Int      @id @default(autoincrement())
  userId          Int      @map("user_id")
  accountId       Int      @map("account_id")
  permissionLevel String   @default("full") @map("permission_level") @db.VarChar(20)
  assignedAt      DateTime @default(now()) @map("assigned_at")
  assignedBy      Int?     @map("assigned_by")

  // Relations
  user            User        @relation(fields: [userId], references: [id], onDelete: Cascade)
  account         EbayAccount @relation(fields: [accountId], references: [id], onDelete: Cascade)
  assignedByUser  User?       @relation("AssignedBy", fields: [assignedBy], references: [id])

  @@unique([userId, accountId])
  @@map("user_account_permissions")
}

model SyncHistory {
  id               Int      @id @default(autoincrement())
  accountId        Int      @map("account_id")
  syncType         String   @map("sync_type") @db.VarChar(50)
  fileName         String?  @map("file_name") @db.VarChar(255)
  fileSize         BigInt?  @map("file_size")
  recordsProcessed Int      @default(0) @map("records_processed")
  recordsSuccess   Int      @default(0) @map("records_success")
  recordsFailed    Int      @default(0) @map("records_failed")
  syncStatus       String   @default("pending") @map("sync_status") @db.VarChar(20)
  errorMessage     String?  @map("error_message")
  startedAt        DateTime @default(now()) @map("started_at")
  completedAt      DateTime? @map("completed_at")
  processingTime   Int?     @map("processing_time")

  // Relations
  account          EbayAccount @relation(fields: [accountId], references: [id], onDelete: Cascade)

  @@map("sync_history")
}
```

### 3. Environment Configuration
```typescript
// src/config/environment.ts
import dotenv from 'dotenv';
import { z } from 'zod';

dotenv.config();

const envSchema = z.object({
  NODE_ENV: z.enum(['development', 'production', 'test']).default('development'),
  PORT: z.string().transform(Number).default('3000'),
  DATABASE_URL: z.string(),
  JWT_SECRET: z.string(),
  JWT_EXPIRES_IN: z.string().default('24h'),
  UPLOAD_DIR: z.string().default('./uploads'),
  MAX_FILE_SIZE: z.string().transform(Number).default('10485760'), // 10MB
  BCRYPT_ROUNDS: z.string().transform(Number).default('12'),
  RATE_LIMIT_WINDOW: z.string().transform(Number).default('900000'), // 15 minutes
  RATE_LIMIT_MAX: z.string().transform(Number).default('100')
});

export const env = envSchema.parse(process.env);
```

### 4. Database Configuration
```typescript
// src/config/database.ts
import { PrismaClient } from '@prisma/client';
import { env } from './environment';

let prisma: PrismaClient;

declare global {
  var __prisma: PrismaClient | undefined;
}

if (env.NODE_ENV === 'production') {
  prisma = new PrismaClient();
} else {
  if (!global.__prisma) {
    global.__prisma = new PrismaClient({
      log: ['query', 'error', 'warn'],
    });
  }
  prisma = global.__prisma;
}

export { prisma };

// Connection test
export async function testDatabaseConnection() {
  try {
    await prisma.$connect();
    console.log('✅ Database connected successfully');
    return true;
  } catch (error) {
    console.error('❌ Database connection failed:', error);
    return false;
  }
}

// Graceful shutdown
export async function disconnectDatabase() {
  await prisma.$disconnect();
}
```

### 5. Validation Schemas
```typescript
// src/schemas/user.schema.ts
import { z } from 'zod';

export const createUserSchema = z.object({
  username: z.string().min(3).max(50).regex(/^[a-zA-Z0-9_]+$/),
  email: z.string().email().max(255),
  password: z.string().min(8).max(100),
  fullName: z.string().min(1).max(255).optional(),
  role: z.enum(['super_admin', 'manager', 'operator', 'viewer']).default('operator'),
  maxAccountsAllowed: z.number().min(1).max(10).default(3)
});

export const updateUserSchema = createUserSchema.partial().omit({ password: true });

export const changePasswordSchema = z.object({
  currentPassword: z.string(),
  newPassword: z.string().min(8).max(100)
});

export const loginSchema = z.object({
  username: z.string(),
  password: z.string()
});

export type CreateUserInput = z.infer<typeof createUserSchema>;
export type UpdateUserInput = z.infer<typeof updateUserSchema>;
export type ChangePasswordInput = z.infer<typeof changePasswordSchema>;
export type LoginInput = z.infer<typeof loginSchema>;
```

```typescript
// src/schemas/account.schema.ts
import { z } from 'zod';

export const createEbayAccountSchema = z.object({
  accountName: z.string().min(1).max(100),
  accountEmail: z.string().email().max(255),
  ebayUsername: z.string().max(100).optional(),
  browserProfilePath: z.string().max(500).optional(),
  syncFrequency: z.number().min(60).max(1440).default(240), // 1 hour to 24 hours
  notes: z.string().max(1000).optional()
});

export const updateEbayAccountSchema = createEbayAccountSchema.partial();

export const assignAccountPermissionSchema = z.object({
  userId: z.number().positive(),
  accountId: z.number().positive(),
  permissionLevel: z.enum(['full', 'read_only', 'limited']).default('full')
});

export type CreateEbayAccountInput = z.infer<typeof createEbayAccountSchema>;
export type UpdateEbayAccountInput = z.infer<typeof updateEbayAccountSchema>;
export type AssignAccountPermissionInput = z.infer<typeof assignAccountPermissionSchema>;
```

### 6. TypeScript Types
```typescript
// src/types/common.types.ts
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  message?: string;
  error?: string;
  meta?: {
    page?: number;
    limit?: number;
    total?: number;
    totalPages?: number;
  };
}

export interface PaginationParams {
  page?: number;
  limit?: number;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
}

export interface FilterParams {
  search?: string;
  status?: string;
  startDate?: string;
  endDate?: string;
}

export type UserRole = 'super_admin' | 'manager' | 'operator' | 'viewer';
export type AccountStatus = 'active' | 'suspended' | 'inactive';
export type PermissionLevel = 'full' | 'read_only' | 'limited';
export type SyncStatus = 'pending' | 'processing' | 'completed' | 'failed';
export type SyncType = 'orders' | 'listings' | 'products' | 'messages';
```

### 7. Docker Configuration
```yaml
# docker-compose.yml
version: '3.8'

services:
  postgres:
    image: postgres:15
    container_name: ebay_postgres
    environment:
      POSTGRES_DB: ebay_management
      POSTGRES_USER: ebay_user
      POSTGRES_PASSWORD: ebay_password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init-db.sql:/docker-entrypoint-initdb.d/init-db.sql
    networks:
      - ebay_network

  redis:
    image: redis:7-alpine
    container_name: ebay_redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    networks:
      - ebay_network

  adminer:
    image: adminer
    container_name: ebay_adminer
    ports:
      - "8080:8080"
    networks:
      - ebay_network

volumes:
  postgres_data:
  redis_data:

networks:
  ebay_network:
    driver: bridge
```

### 8. Environment Example
```env
# .env.example
NODE_ENV=development
PORT=3000

# Database
DATABASE_URL="postgresql://ebay_user:ebay_password@localhost:5432/ebay_management"

# JWT
JWT_SECRET="your-super-secret-jwt-key-here"
JWT_EXPIRES_IN="24h"

# File Upload
UPLOAD_DIR="./uploads"
MAX_FILE_SIZE=10485760

# Security
BCRYPT_ROUNDS=12
RATE_LIMIT_WINDOW=900000
RATE_LIMIT_MAX=100

# Redis
REDIS_URL="redis://localhost:6379"
```

## Implementation Commands

### Setup Database
```bash
# Start database
docker-compose up -d postgres redis

# Generate Prisma client
npm run db:generate

# Run migrations
npm run db:migrate

# View database
npm run db:studio
```

### Development
```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Run tests
npm test

# Build for production
npm run build
```

## Testing Requirements

### Unit Tests
- User model validation
- Account model validation
- Database connection
- Schema validation
- Utility functions

### Integration Tests
- Database CRUD operations
- User-Account relationships
- Permission assignments
- Sync history tracking

## Success Criteria

1. ✅ Database schema created and migrated
2. ✅ Prisma models generating correctly
3. ✅ Environment configuration working
4. ✅ Docker containers running
5. ✅ TypeScript types defined
6. ✅ Validation schemas working
7. ✅ Test suite foundation ready

## Next Steps
- Plan 2: Implement authentication & user management APIs
- Plan 3: Create CSV processing engine
- Plan 4: Build order management module