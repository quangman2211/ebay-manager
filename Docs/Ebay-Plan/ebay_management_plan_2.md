# Plan 2: Authentication & User Management APIs

## Objective
Implement authentication system, user management APIs, and account permission management with JWT-based security.

## Dependencies
- Plan 1: Database Setup & Foundation must be completed

## Implementation Files

### 1. JWT Utilities
```typescript
// src/utils/jwt.ts
import jwt from 'jsonwebtoken';
import { env } from '../config/environment';

export interface JWTPayload {
  userId: number;
  username: string;
  role: string;
  accountIds: number[];
}

export const generateToken = (payload: JWTPayload): string => {
  return jwt.sign(payload, env.JWT_SECRET, {
    expiresIn: env.JWT_EXPIRES_IN,
    issuer: 'ebay-management-system',
  });
};

export const verifyToken = (token: string): JWTPayload => {
  try {
    const decoded = jwt.verify(token, env.JWT_SECRET) as JWTPayload;
    return decoded;
  } catch (error) {
    throw new Error('Invalid or expired token');
  }
};

export const refreshToken = (token: string): string => {
  const decoded = verifyToken(token);
  // Create new token with same payload
  return generateToken({
    userId: decoded.userId,
    username: decoded.username,
    role: decoded.role,
    accountIds: decoded.accountIds,
  });
};
```

### 2. Password Utilities
```typescript
// src/utils/password.ts
import bcrypt from 'bcryptjs';
import { env } from '../config/environment';

export const hashPassword = async (password: string): Promise<string> => {
  return await bcrypt.hash(password, env.BCRYPT_ROUNDS);
};

export const comparePassword = async (
  password: string,
  hashedPassword: string
): Promise<boolean> => {
  return await bcrypt.compare(password, hashedPassword);
};

export const validatePasswordStrength = (password: string): {
  isValid: boolean;
  errors: string[];
} => {
  const errors: string[] = [];
  
  if (password.length < 8) {
    errors.push('Password must be at least 8 characters long');
  }
  
  if (!/[a-z]/.test(password)) {
    errors.push('Password must contain at least one lowercase letter');
  }
  
  if (!/[A-Z]/.test(password)) {
    errors.push('Password must contain at least one uppercase letter');
  }
  
  if (!/\d/.test(password)) {
    errors.push('Password must contain at least one number');
  }
  
  if (!/[!@#$%^&*(),.?":{}|<>]/.test(password)) {
    errors.push('Password must contain at least one special character');
  }
  
  return {
    isValid: errors.length === 0,
    errors,
  };
};
```

### 3. Authentication Middleware
```typescript
// src/middleware/auth.middleware.ts
import { Request, Response, NextFunction } from 'express';
import { verifyToken, JWTPayload } from '../utils/jwt';
import { ApiResponse } from '../types/common.types';

declare global {
  namespace Express {
    interface Request {
      user?: JWTPayload;
    }
  }
}

export const authenticate = (
  req: Request,
  res: Response<ApiResponse>,
  next: NextFunction
) => {
  try {
    const authHeader = req.headers.authorization;
    
    if (!authHeader) {
      return res.status(401).json({
        success: false,
        error: 'No authorization header provided',
      });
    }
    
    const token = authHeader.split(' ')[1]; // Bearer <token>
    
    if (!token) {
      return res.status(401).json({
        success: false,
        error: 'No token provided',
      });
    }
    
    const decoded = verifyToken(token);
    req.user = decoded;
    
    next();
  } catch (error) {
    return res.status(401).json({
      success: false,
      error: 'Invalid or expired token',
    });
  }
};

export const authorize = (roles: string[]) => {
  return (req: Request, res: Response<ApiResponse>, next: NextFunction) => {
    if (!req.user) {
      return res.status(401).json({
        success: false,
        error: 'Authentication required',
      });
    }
    
    if (!roles.includes(req.user.role)) {
      return res.status(403).json({
        success: false,
        error: 'Insufficient permissions',
      });
    }
    
    next();
  };
};

export const checkAccountAccess = (
  req: Request,
  res: Response<ApiResponse>,
  next: NextFunction
) => {
  if (!req.user) {
    return res.status(401).json({
      success: false,
      error: 'Authentication required',
    });
  }
  
  const accountId = parseInt(req.params.accountId || req.body.accountId);
  
  if (!accountId) {
    return res.status(400).json({
      success: false,
      error: 'Account ID is required',
    });
  }
  
  // Super admin can access all accounts
  if (req.user.role === 'super_admin') {
    return next();
  }
  
  // Check if user has access to this account
  if (!req.user.accountIds.includes(accountId)) {
    return res.status(403).json({
      success: false,
      error: 'Access denied to this account',
    });
  }
  
  next();
};
```

### 4. User Service
```typescript
// src/services/user.service.ts
import { prisma } from '../config/database';
import { hashPassword, comparePassword } from '../utils/password';
import { generateToken } from '../utils/jwt';
import {
  CreateUserInput,
  UpdateUserInput,
  ChangePasswordInput,
  LoginInput,
} from '../schemas/user.schema';
import { PaginationParams, FilterParams } from '../types/common.types';

export class UserService {
  async createUser(data: CreateUserInput) {
    // Check if user already exists
    const existingUser = await prisma.user.findFirst({
      where: {
        OR: [
          { email: data.email },
          { username: data.username },
        ],
      },
    });
    
    if (existingUser) {
      throw new Error('User with this email or username already exists');
    }
    
    // Hash password
    const passwordHash = await hashPassword(data.password);
    
    // Create user
    const user = await prisma.user.create({
      data: {
        username: data.username,
        email: data.email,
        passwordHash,
        fullName: data.fullName,
        role: data.role || 'operator',
        maxAccountsAllowed: data.maxAccountsAllowed || 3,
      },
      select: {
        id: true,
        username: true,
        email: true,
        fullName: true,
        role: true,
        maxAccountsAllowed: true,
        isActive: true,
        createdAt: true,
        updatedAt: true,
      },
    });
    
    return user;
  }
  
  async login(data: LoginInput) {
    // Find user by username or email
    const user = await prisma.user.findFirst({
      where: {
        OR: [
          { username: data.username },
          { email: data.username },
        ],
        isActive: true,
      },
      include: {
        accountPermissions: {
          include: {
            account: {
              select: {
                id: true,
                accountName: true,
                isActive: true,
              },
            },
          },
          where: {
            account: {
              isActive: true,
            },
          },
        },
      },
    });
    
    if (!user) {
      throw new Error('Invalid credentials');
    }
    
    // Verify password
    const isValidPassword = await comparePassword(data.password, user.passwordHash);
    
    if (!isValidPassword) {
      throw new Error('Invalid credentials');
    }
    
    // Update last login
    await prisma.user.update({
      where: { id: user.id },
      data: { lastLogin: new Date() },
    });
    
    // Get accessible account IDs
    const accountIds = user.accountPermissions.map(p => p.account.id);
    
    // Generate JWT token
    const token = generateToken({
      userId: user.id,
      username: user.username,
      role: user.role,
      accountIds,
    });
    
    return {
      user: {
        id: user.id,
        username: user.username,
        email: user.email,
        fullName: user.fullName,
        role: user.role,
        maxAccountsAllowed: user.maxAccountsAllowed,
        accounts: user.accountPermissions.map(p => ({
          id: p.account.id,
          name: p.account.accountName,
          permissionLevel: p.permissionLevel,
        })),
      },
      token,
    };
  }
  
  async getUserById(id: number) {
    const user = await prisma.user.findUnique({
      where: { id },
      select: {
        id: true,
        username: true,
        email: true,
        fullName: true,
        role: true,
        maxAccountsAllowed: true,
        isActive: true,
        lastLogin: true,
        createdAt: true,
        updatedAt: true,
        accountPermissions: {
          include: {
            account: {
              select: {
                id: true,
                accountName: true,
                accountEmail: true,
                isActive: true,
              },
            },
          },
        },
      },
    });
    
    if (!user) {
      throw new Error('User not found');
    }
    
    return {
      ...user,
      accounts: user.accountPermissions.map(p => ({
        id: p.account.id,
        name: p.account.accountName,
        email: p.account.accountEmail,
        permissionLevel: p.permissionLevel,
        assignedAt: p.assignedAt,
      })),
      accountPermissions: undefined,
    };
  }
  
  async getUsers(pagination: PaginationParams, filters: FilterParams) {
    const { page = 1, limit = 20, sortBy = 'createdAt', sortOrder = 'desc' } = pagination;
    const { search, status } = filters;
    
    const skip = (page - 1) * limit;
    
    const where: any = {};
    
    if (search) {
      where.OR = [
        { username: { contains: search, mode: 'insensitive' } },
        { email: { contains: search, mode: 'insensitive' } },
        { fullName: { contains: search, mode: 'insensitive' } },
      ];
    }
    
    if (status === 'active' || status === 'inactive') {
      where.isActive = status === 'active';
    }
    
    const [users, total] = await Promise.all([
      prisma.user.findMany({
        where,
        select: {
          id: true,
          username: true,
          email: true,
          fullName: true,
          role: true,
          maxAccountsAllowed: true,
          isActive: true,
          lastLogin: true,
          createdAt: true,
          _count: {
            select: {
              accountPermissions: true,
            },
          },
        },
        skip,
        take: limit,
        orderBy: { [sortBy]: sortOrder },
      }),
      prisma.user.count({ where }),
    ]);
    
    return {
      users: users.map(user => ({
        ...user,
        accountCount: user._count.accountPermissions,
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
  
  async updateUser(id: number, data: UpdateUserInput) {
    const user = await prisma.user.update({
      where: { id },
      data: {
        username: data.username,
        email: data.email,
        fullName: data.fullName,
        role: data.role,
        maxAccountsAllowed: data.maxAccountsAllowed,
      },
      select: {
        id: true,
        username: true,
        email: true,
        fullName: true,
        role: true,
        maxAccountsAllowed: true,
        isActive: true,
        updatedAt: true,
      },
    });
    
    return user;
  }
  
  async changePassword(userId: number, data: ChangePasswordInput) {
    const user = await prisma.user.findUnique({
      where: { id: userId },
      select: { passwordHash: true },
    });
    
    if (!user) {
      throw new Error('User not found');
    }
    
    // Verify current password
    const isValidPassword = await comparePassword(
      data.currentPassword,
      user.passwordHash
    );
    
    if (!isValidPassword) {
      throw new Error('Current password is incorrect');
    }
    
    // Hash new password
    const newPasswordHash = await hashPassword(data.newPassword);
    
    // Update password
    await prisma.user.update({
      where: { id: userId },
      data: { passwordHash: newPasswordHash },
    });
    
    return { success: true };
  }
  
  async toggleUserStatus(id: number) {
    const user = await prisma.user.findUnique({
      where: { id },
      select: { isActive: true },
    });
    
    if (!user) {
      throw new Error('User not found');
    }
    
    const updatedUser = await prisma.user.update({
      where: { id },
      data: { isActive: !user.isActive },
      select: {
        id: true,
        username: true,
        email: true,
        isActive: true,
        updatedAt: true,
      },
    });
    
    return updatedUser;
  }
  
  async deleteUser(id: number) {
    // Check if user has any accounts
    const accountCount = await prisma.userAccountPermission.count({
      where: { userId: id },
    });
    
    if (accountCount > 0) {
      throw new Error('Cannot delete user with assigned accounts. Remove account assignments first.');
    }
    
    await prisma.user.delete({
      where: { id },
    });
    
    return { success: true };
  }
}
```

### 5. Account Service
```typescript
// src/services/account.service.ts
import { prisma } from '../config/database';
import {
  CreateEbayAccountInput,
  UpdateEbayAccountInput,
  AssignAccountPermissionInput,
} from '../schemas/account.schema';
import { PaginationParams, FilterParams } from '../types/common.types';

export class AccountService {
  async createAccount(userId: number, data: CreateEbayAccountInput) {
    // Check user's account limit
    const user = await prisma.user.findUnique({
      where: { id: userId },
      select: { maxAccountsAllowed: true },
    });
    
    if (!user) {
      throw new Error('User not found');
    }
    
    const currentAccountCount = await prisma.userAccountPermission.count({
      where: { userId },
    });
    
    if (currentAccountCount >= user.maxAccountsAllowed) {
      throw new Error(`User has reached maximum account limit (${user.maxAccountsAllowed})`);
    }
    
    // Create account
    const account = await prisma.$transaction(async (tx) => {
      // Create eBay account
      const newAccount = await tx.ebayAccount.create({
        data: {
          userId,
          accountName: data.accountName,
          accountEmail: data.accountEmail,
          ebayUsername: data.ebayUsername,
          browserProfilePath: data.browserProfilePath,
          syncFrequency: data.syncFrequency || 240,
          notes: data.notes,
        },
      });
      
      // Assign permission to the creating user
      await tx.userAccountPermission.create({
        data: {
          userId,
          accountId: newAccount.id,
          permissionLevel: 'full',
          assignedBy: userId,
        },
      });
      
      return newAccount;
    });
    
    return account;
  }
  
  async getAccountsByUser(userId: number, userRole: string) {
    const where: any = {};
    
    // Super admin can see all accounts
    if (userRole !== 'super_admin') {
      where.accountPermissions = {
        some: { userId },
      };
    }
    
    const accounts = await prisma.ebayAccount.findMany({
      where,
      select: {
        id: true,
        accountName: true,
        accountEmail: true,
        ebayUsername: true,
        accountStatus: true,
        lastSyncAt: true,
        syncFrequency: true,
        isActive: true,
        createdAt: true,
        user: {
          select: {
            id: true,
            username: true,
            fullName: true,
          },
        },
        accountPermissions: {
          where: userRole !== 'super_admin' ? { userId } : undefined,
          select: {
            permissionLevel: true,
            assignedAt: true,
          },
        },
        _count: {
          select: {
            syncHistory: true,
          },
        },
      },
    });
    
    return accounts.map(account => ({
      ...account,
      permissionLevel: account.accountPermissions[0]?.permissionLevel || null,
      syncCount: account._count.syncHistory,
      _count: undefined,
      accountPermissions: undefined,
    }));
  }
  
  async getAccountById(accountId: number) {
    const account = await prisma.ebayAccount.findUnique({
      where: { id: accountId },
      include: {
        user: {
          select: {
            id: true,
            username: true,
            fullName: true,
          },
        },
        accountPermissions: {
          include: {
            user: {
              select: {
                id: true,
                username: true,
                fullName: true,
              },
            },
          },
        },
        syncHistory: {
          select: {
            id: true,
            syncType: true,
            syncStatus: true,
            recordsProcessed: true,
            startedAt: true,
            completedAt: true,
          },
          orderBy: { startedAt: 'desc' },
          take: 5,
        },
      },
    });
    
    if (!account) {
      throw new Error('Account not found');
    }
    
    return {
      ...account,
      permissions: account.accountPermissions.map(p => ({
        userId: p.user.id,
        username: p.user.username,
        fullName: p.user.fullName,
        permissionLevel: p.permissionLevel,
        assignedAt: p.assignedAt,
      })),
      recentSyncs: account.syncHistory,
      accountPermissions: undefined,
      syncHistory: undefined,
    };
  }
  
  async updateAccount(accountId: number, data: UpdateEbayAccountInput) {
    const account = await prisma.ebayAccount.update({
      where: { id: accountId },
      data: {
        accountName: data.accountName,
        accountEmail: data.accountEmail,
        ebayUsername: data.ebayUsername,
        browserProfilePath: data.browserProfilePath,
        syncFrequency: data.syncFrequency,
        notes: data.notes,
      },
    });
    
    return account;
  }
  
  async assignAccountPermission(data: AssignAccountPermissionInput, assignedBy: number) {
    // Check if user already has permission for this account
    const existingPermission = await prisma.userAccountPermission.findUnique({
      where: {
        userId_accountId: {
          userId: data.userId,
          accountId: data.accountId,
        },
      },
    });
    
    if (existingPermission) {
      // Update existing permission
      return await prisma.userAccountPermission.update({
        where: {
          userId_accountId: {
            userId: data.userId,
            accountId: data.accountId,
          },
        },
        data: {
          permissionLevel: data.permissionLevel,
          assignedBy,
        },
      });
    }
    
    // Check user's account limit
    const user = await prisma.user.findUnique({
      where: { id: data.userId },
      select: { maxAccountsAllowed: true },
    });
    
    if (!user) {
      throw new Error('User not found');
    }
    
    const currentAccountCount = await prisma.userAccountPermission.count({
      where: { userId: data.userId },
    });
    
    if (currentAccountCount >= user.maxAccountsAllowed) {
      throw new Error(`User has reached maximum account limit (${user.maxAccountsAllowed})`);
    }
    
    // Create new permission
    return await prisma.userAccountPermission.create({
      data: {
        userId: data.userId,
        accountId: data.accountId,
        permissionLevel: data.permissionLevel,
        assignedBy,
      },
    });
  }
  
  async removeAccountPermission(userId: number, accountId: number) {
    const permission = await prisma.userAccountPermission.findUnique({
      where: {
        userId_accountId: {
          userId,
          accountId,
        },
      },
    });
    
    if (!permission) {
      throw new Error('Permission not found');
    }
    
    await prisma.userAccountPermission.delete({
      where: {
        userId_accountId: {
          userId,
          accountId,
        },
      },
    });
    
    return { success: true };
  }
  
  async toggleAccountStatus(accountId: number) {
    const account = await prisma.ebayAccount.findUnique({
      where: { id: accountId },
      select: { isActive: true },
    });
    
    if (!account) {
      throw new Error('Account not found');
    }
    
    const updatedAccount = await prisma.ebayAccount.update({
      where: { id: accountId },
      data: { isActive: !account.isActive },
    });
    
    return updatedAccount;
  }
  
  async deleteAccount(accountId: number) {
    // Check if account has any sync history or other related data
    const syncCount = await prisma.syncHistory.count({
      where: { accountId },
    });
    
    if (syncCount > 0) {
      throw new Error('Cannot delete account with sync history. Archive it instead.');
    }
    
    await prisma.ebayAccount.delete({
      where: { id: accountId },
    });
    
    return { success: true };
  }
}
```

### 6. Authentication Controller
```typescript
// src/controllers/auth.controller.ts
import { Request, Response } from 'express';
import { UserService } from '../services/user.service';
import { loginSchema, createUserSchema, changePasswordSchema } from '../schemas/user.schema';
import { validatePasswordStrength } from '../utils/password';
import { ApiResponse } from '../types/common.types';

const userService = new UserService();

export class AuthController {
  async register(req: Request, res: Response<ApiResponse>) {
    try {
      const validatedData = createUserSchema.parse(req.body);
      
      // Validate password strength
      const passwordValidation = validatePasswordStrength(validatedData.password);
      if (!passwordValidation.isValid) {
        return res.status(400).json({
          success: false,
          error: 'Password does not meet requirements',
          data: { errors: passwordValidation.errors },
        });
      }
      
      const user = await userService.createUser(validatedData);
      
      res.status(201).json({
        success: true,
        data: user,
        message: 'User created successfully',
      });
    } catch (error) {
      res.status(400).json({
        success: false,
        error: error instanceof Error ? error.message : 'Registration failed',
      });
    }
  }
  
  async login(req: Request, res: Response<ApiResponse>) {
    try {
      const validatedData = loginSchema.parse(req.body);
      const result = await userService.login(validatedData);
      
      res.json({
        success: true,
        data: result,
        message: 'Login successful',
      });
    } catch (error) {
      res.status(401).json({
        success: false,
        error: error instanceof Error ? error.message : 'Login failed',
      });
    }
  }
  
  async me(req: Request, res: Response<ApiResponse>) {
    try {
      if (!req.user) {
        return res.status(401).json({
          success: false,
          error: 'Not authenticated',
        });
      }
      
      const user = await userService.getUserById(req.user.userId);
      
      res.json({
        success: true,
        data: user,
      });
    } catch (error) {
      res.status(500).json({
        success: false,
        error: error instanceof Error ? error.message : 'Failed to get user info',
      });
    }
  }
  
  async changePassword(req: Request, res: Response<ApiResponse>) {
    try {
      if (!req.user) {
        return res.status(401).json({
          success: false,
          error: 'Not authenticated',
        });
      }
      
      const validatedData = changePasswordSchema.parse(req.body);
      
      // Validate new password strength
      const passwordValidation = validatePasswordStrength(validatedData.newPassword);
      if (!passwordValidation.isValid) {
        return res.status(400).json({
          success: false,
          error: 'New password does not meet requirements',
          data: { errors: passwordValidation.errors },
        });
      }
      
      await userService.changePassword(req.user.userId, validatedData);
      
      res.json({
        success: true,
        message: 'Password changed successfully',
      });
    } catch (error) {
      res.status(400).json({
        success: false,
        error: error instanceof Error ? error.message : 'Password change failed',
      });
    }
  }
  
  async logout(req: Request, res: Response<ApiResponse>) {
    // In a stateless JWT system, logout is handled client-side
    // But we can add token blacklisting here if needed
    res.json({
      success: true,
      message: 'Logged out successfully',
    });
  }
}
```

### 7. User Management Controller
```typescript
// src/controllers/user.controller.ts
import { Request, Response } from 'express';
import { UserService } from '../services/user.service';
import { createUserSchema, updateUserSchema } from '../schemas/user.schema';
import { ApiResponse } from '../types/common.types';

const userService = new UserService();

export class UserController {
  async getUsers(req: Request, res: Response<ApiResponse>) {
    try {
      const page = parseInt(req.query.page as string) || 1;
      const limit = parseInt(req.query.limit as string) || 20;
      const sortBy = req.query.sortBy as string || 'createdAt';
      const sortOrder = (req.query.sortOrder as 'asc' | 'desc') || 'desc';
      const search = req.query.search as string;
      const status = req.query.status as string;
      
      const result = await userService.getUsers(
        { page, limit, sortBy, sortOrder },
        { search, status }
      );
      
      res.json({
        success: true,
        data: result.users,
        meta: result.pagination,
      });
    } catch (error) {
      res.status(500).json({
        success: false,
        error: error instanceof Error ? error.message : 'Failed to get users',
      });
    }
  }
  
  async getUserById(req: Request, res: Response<ApiResponse>) {
    try {
      const userId = parseInt(req.params.id);
      const user = await userService.getUserById(userId);
      
      res.json({
        success: true,
        data: user,
      });
    } catch (error) {
      res.status(404).json({
        success: false,
        error: error instanceof Error ? error.message : 'User not found',
      });
    }
  }
  
  async createUser(req: Request, res: Response<ApiResponse>) {
    try {
      const validatedData = createUserSchema.parse(req.body);
      const user = await userService.createUser(validatedData);
      
      res.status(201).json({
        success: true,
        data: user,
        message: 'User created successfully',
      });
    } catch (error) {
      res.status(400).json({
        success: false,
        error: error instanceof Error ? error.message : 'Failed to create user',
      });
    }
  }
  
  async updateUser(req: Request, res: Response<ApiResponse>) {
    try {
      const userId = parseInt(req.params.id);
      const validatedData = updateUserSchema.parse(req.body);
      
      const user = await userService.updateUser(userId, validatedData);
      
      res.json({
        success: true,
        data: user,
        message: 'User updated successfully',
      });
    } catch (error) {
      res.status(400).json({
        success: false,
        error: error instanceof Error ? error.message : 'Failed to update user',
      });
    }
  }
  
  async toggleUserStatus(req: Request, res: Response<ApiResponse>) {
    try {
      const userId = parseInt(req.params.id);
      const user = await userService.toggleUserStatus(userId);
      
      res.json({
        success: true,
        data: user,
        message: `User ${user.isActive ? 'activated' : 'deactivated'} successfully`,
      });
    } catch (error) {
      res.status(400).json({
        success: false,
        error: error instanceof Error ? error.message : 'Failed to update user status',
      });
    }
  }
  
  async deleteUser(req: Request, res: Response<ApiResponse>) {
    try {
      const userId = parseInt(req.params.id);
      
      // Prevent users from deleting themselves
      if (req.user?.userId === userId) {
        return res.status(400).json({
          success: false,
          error: 'Cannot delete your own account',
        });
      }
      
      await userService.deleteUser(userId);
      
      res.json({
        success: true,
        message: 'User deleted successfully',
      });
    } catch (error) {
      res.status(400).json({
        success: false,
        error: error instanceof Error ? error.message : 'Failed to delete user',
      });
    }
  }
}
```

### 8. API Routes
```typescript
// src/routes/auth.routes.ts
import { Router } from 'express';
import { AuthController } from '../controllers/auth.controller';
import { authenticate, authorize } from '../middleware/auth.middleware';

const router = Router();
const authController = new AuthController();

// Public routes
router.post('/register', authController.register.bind(authController));
router.post('/login', authController.login.bind(authController));

// Protected routes
router.get('/me', authenticate, authController.me.bind(authController));
router.post('/change-password', authenticate, authController.changePassword.bind(authController));
router.post('/logout', authenticate, authController.logout.bind(authController));

export default router;
```

```typescript
// src/routes/user.routes.ts
import { Router } from 'express';
import { UserController } from '../controllers/user.controller';
import { authenticate, authorize } from '../middleware/auth.middleware';

const router = Router();
const userController = new UserController();

// All routes require authentication and admin/manager role
router.use(authenticate);
router.use(authorize(['super_admin', 'manager']));

router.get('/', userController.getUsers.bind(userController));
router.get('/:id', userController.getUserById.bind(userController));
router.post('/', userController.createUser.bind(userController));
router.put('/:id', userController.updateUser.bind(userController));
router.patch('/:id/toggle-status', userController.toggleUserStatus.bind(userController));
router.delete('/:id', userController.deleteUser.bind(userController));

export default router;
```

### 9. Main App Setup
```typescript
// src/app.ts
import express from 'express';
import helmet from 'helmet';
import cors from 'cors';
import compression from 'compression';
import rateLimit from 'express-rate-limit';
import { env } from './config/environment';
import { testDatabaseConnection } from './config/database';
import authRoutes from './routes/auth.routes';
import userRoutes from './routes/user.routes';

const app = express();

// Security middleware
app.use(helmet());
app.use(cors({
  origin: process.env.FRONTEND_URL || 'http://localhost:3000',
  credentials: true,
}));

// Rate limiting
const limiter = rateLimit({
  windowMs: env.RATE_LIMIT_WINDOW,
  max: env.RATE_LIMIT_MAX,
  message: { success: false, error: 'Too many requests' },
});
app.use(limiter);

// Body parsing & compression
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true }));
app.use(compression());

// Health check
app.get('/health', (req, res) => {
  res.json({ success: true, message: 'API is running' });
});

// Routes
app.use('/api/auth', authRoutes);
app.use('/api/users', userRoutes);

// 404 handler
app.use('*', (req, res) => {
  res.status(404).json({
    success: false,
    error: 'Route not found',
  });
});

// Error handler
app.use((err: any, req: express.Request, res: express.Response, next: express.NextFunction) => {
  console.error(err);
  res.status(500).json({
    success: false,
    error: 'Internal server error',
  });
});

export default app;
```

```typescript
// src/server.ts
import app from './app';
import { env } from './config/environment';
import { testDatabaseConnection, disconnectDatabase } from './config/database';

async function startServer() {
  try {
    // Test database connection
    await testDatabaseConnection();
    
    const server = app.listen(env.PORT, () => {
      console.log(`🚀 Server running on port ${env.PORT}`);
      console.log(`📝 Environment: ${env.NODE_ENV}`);
    });
    
    // Graceful shutdown
    process.on('SIGTERM', async () => {
      console.log('SIGTERM received, shutting down gracefully');
      server.close(async () => {
        await disconnectDatabase();
        process.exit(0);
      });
    });
    
    process.on('SIGINT', async () => {
      console.log('SIGINT received, shutting down gracefully');
      server.close(async () => {
        await disconnectDatabase();
        process.exit(0);
      });
    });
    
  } catch (error) {
    console.error('Failed to start server:', error);
    process.exit(1);
  }
}

startServer();
```

## Testing Implementation

### Unit Tests
```typescript
// tests/unit/auth.test.ts
import { generateToken, verifyToken } from '../../src/utils/jwt';
import { hashPassword, comparePassword } from '../../src/utils/password';

describe('JWT Utils', () => {
  test('should generate and verify token', () => {
    const payload = {
      userId: 1,
      username: 'testuser',
      role: 'operator',
      accountIds: [1, 2],
    };
    
    const token = generateToken(payload);
    const decoded = verifyToken(token);
    
    expect(decoded.userId).toBe(payload.userId);
    expect(decoded.username).toBe(payload.username);
  });
});

describe('Password Utils', () => {
  test('should hash and compare password', async () => {
    const password = 'TestPassword123!';
    const hashedPassword = await hashPassword(password);
    
    const isValid = await comparePassword(password, hashedPassword);
    expect(isValid).toBe(true);
    
    const isInvalid = await comparePassword('wrongpassword', hashedPassword);
    expect(isInvalid).toBe(false);
  });
});
```

## Success Criteria

1. ✅ JWT authentication working
2. ✅ User registration/login APIs
3. ✅ Password validation & hashing
4. ✅ Role-based access control
5. ✅ Account permission system
6. ✅ API security middleware
7. ✅ Error handling & validation
8. ✅ Unit tests passing

## Next Steps
- Plan 3: CSV Processing Engine
- Plan 4: Order Management Module