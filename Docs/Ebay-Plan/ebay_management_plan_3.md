# Plan 3: CSV Processing Engine

## Objective
Create robust CSV processing engine for eBay data synchronization with file validation, parsing, transformation, and error handling.

## Dependencies
- Plan 1: Database Setup & Foundation completed
- Plan 2: Authentication & User Management APIs completed

## File Structure Updates
```
src/
├── services/
│   ├── csv-processor.service.ts
│   ├── file-upload.service.ts
│   └── data-mapper.service.ts
├── middleware/
│   ├── file-upload.middleware.ts
│   └── csv-validation.middleware.ts
├── utils/
│   ├── csv-parser.ts
│   ├── file-validator.ts
│   └── data-transformer.ts
├── schemas/
│   ├── csv-schemas.ts
│   └── upload.schema.ts
├── types/
│   ├── csv.types.ts
│   └── upload.types.ts
├── controllers/
│   └── upload.controller.ts
├── routes/
│   └── upload.routes.ts
└── config/
    └── upload.config.ts
```

## Implementation Files

### 1. CSV Type Definitions
```typescript
// src/types/csv.types.ts

export interface BaseCSVRecord {
  rowNumber: number;
  rawData: any;
  errors: string[];
  warnings: string[];
}

export interface ActiveListingCSVRecord extends BaseCSVRecord {
  itemNumber: number;
  title: string;
  variationDetails?: string;
  customLabelSKU?: string;
  availableQuantity: number;
  format: string;
  currency: string;
  startPrice: number;
  auctionBuyItNowPrice?: number;
  reservePrice?: number;
  currentPrice: number;
  soldQuantity: number;
  watchers: number;
  bids?: number;
  startDate: Date;
  endDate: Date;
  ebayCategoryName: string;
  ebayCategoryNumber: number;
  condition: string;
  ebayProductId?: string;
  listingSite: string;
  isbn?: string;
  upc?: string;
  ean?: string;
}

export interface OrderCSVRecord extends BaseCSVRecord {
  orderNumber: string;
  buyerUsername: string;
  buyerEmail: string;
  itemNumber: number;
  title: string;
  sku?: string;
  quantity: number;
  unitPrice: number;
  totalPrice: number;
  orderDate: Date;
  paymentDate?: Date;
  shippingDate?: Date;
  trackingNumber?: string;
  shippingAddress: {
    name: string;
    address1: string;
    address2?: string;
    city: string;
    state: string;
    zipCode: string;
    country: string;
  };
}

export interface CSVProcessingResult {
  success: boolean;
  totalRecords: number;
  validRecords: number;
  invalidRecords: number;
  processedRecords: number;
  errors: ProcessingError[];
  warnings: ProcessingWarning[];
  duplicates: number;
  summary: ProcessingSummary;
}

export interface ProcessingError {
  row: number;
  field?: string;
  message: string;
  severity: 'error' | 'warning';
  data?: any;
}

export interface ProcessingWarning {
  row: number;
  field?: string;
  message: string;
  data?: any;
}

export interface ProcessingSummary {
  created: number;
  updated: number;
  skipped: number;
  failed: number;
}

export type CSVType = 
  | 'active_listings'
  | 'sold_orders' 
  | 'awaiting_shipment'
  | 'completed_orders'
  | 'messages'
  | 'products';

export interface CSVFileInfo {
  filename: string;
  size: number;
  mimeType: string;
  encoding: string;
  csvType: CSVType;
  accountId: number;
  uploadedBy: number;
  uploadedAt: Date;
}
```

### 2. CSV Schemas & Validation
```typescript
// src/schemas/csv-schemas.ts
import { z } from 'zod';

// Base schema for all CSV records
const baseRecordSchema = z.object({
  rowNumber: z.number(),
  errors: z.array(z.string()).default([]),
  warnings: z.array(z.string()).default([]),
});

// Active Listings CSV Schema
export const activeListingSchema = baseRecordSchema.extend({
  'Item number': z.union([z.string(), z.number()]).transform(val => 
    typeof val === 'string' ? parseInt(val) : val
  ),
  'Title': z.string().min(1).max(255),
  'Variation details': z.string().optional().nullable(),
  'Custom label (SKU)': z.string().optional().nullable(),
  'Available quantity': z.union([z.string(), z.number()]).transform(val => 
    typeof val === 'string' ? parseInt(val) : val
  ),
  'Format': z.enum(['FIXED_PRICE', 'AUCTION', 'STORE_INVENTORY']),
  'Currency': z.string().length(3),
  'Start price': z.union([z.string(), z.number()]).transform(val => 
    typeof val === 'string' ? parseFloat(val) : val
  ),
  'Current price': z.union([z.string(), z.number()]).transform(val => 
    typeof val === 'string' ? parseFloat(val) : val
  ),
  'Sold quantity': z.union([z.string(), z.number()]).transform(val => 
    typeof val === 'string' ? parseInt(val) : val
  ).default(0),
  'Watchers': z.union([z.string(), z.number()]).transform(val => 
    typeof val === 'string' ? parseInt(val) : val
  ).default(0),
  'Start date': z.string().transform(val => {
    // Handle eBay date format: "Jun-20-25 19:39:11 PDT"
    const date = new Date(val);
    if (isNaN(date.getTime())) {
      throw new Error(`Invalid date format: ${val}`);
    }
    return date;
  }),
  'End date': z.string().transform(val => {
    const date = new Date(val);
    if (isNaN(date.getTime())) {
      throw new Error(`Invalid date format: ${val}`);
    }
    return date;
  }),
  'eBay category 1 name': z.string().min(1),
  'eBay category 1 number': z.union([z.string(), z.number()]).transform(val => 
    typeof val === 'string' ? parseInt(val) : val
  ),
  'Condition': z.string(),
  'eBay Product ID(ePID)': z.union([z.string(), z.number()]).optional().nullable(),
  'Listing site': z.string().default('US'),
  'P:ISBN': z.union([z.string(), z.number()]).optional().nullable(),
  'P:UPC': z.union([z.string(), z.number()]).optional().nullable(),
  'P:EAN': z.union([z.string(), z.number()]).optional().nullable(),
});

// Order CSV Schema
export const orderSchema = baseRecordSchema.extend({
  'Order number': z.string(),
  'Buyer username': z.string(),
  'Buyer email': z.string().email().optional(),
  'Item number': z.union([z.string(), z.number()]).transform(val => 
    typeof val === 'string' ? parseInt(val) : val
  ),
  'Title': z.string(),
  'Custom label (SKU)': z.string().optional().nullable(),
  'Quantity': z.union([z.string(), z.number()]).transform(val => 
    typeof val === 'string' ? parseInt(val) : val
  ),
  'Sale price': z.union([z.string(), z.number()]).transform(val => 
    typeof val === 'string' ? parseFloat(val) : val
  ),
  'Total price': z.union([z.string(), z.number()]).transform(val => 
    typeof val === 'string' ? parseFloat(val) : val
  ),
  'Sale date': z.string().transform(val => new Date(val)),
  'Checkout date': z.string().optional().transform(val => val ? new Date(val) : undefined),
  'Paid date': z.string().optional().transform(val => val ? new Date(val) : undefined),
  'Ship date': z.string().optional().transform(val => val ? new Date(val) : undefined),
  'Tracking number': z.string().optional().nullable(),
  'Buyer name': z.string(),
  'Buyer address 1': z.string(),
  'Buyer address 2': z.string().optional().nullable(),
  'Buyer city': z.string(),
  'Buyer state': z.string(),
  'Buyer zip': z.string(),
  'Buyer country': z.string(),
});

// Upload schema
export const csvUploadSchema = z.object({
  csvType: z.enum(['active_listings', 'sold_orders', 'awaiting_shipment', 'completed_orders', 'messages', 'products']),
  accountId: z.number().positive(),
  replaceExisting: z.boolean().default(false),
  dryRun: z.boolean().default(false),
});

export type ActiveListingCSVInput = z.infer<typeof activeListingSchema>;
export type OrderCSVInput = z.infer<typeof orderSchema>;
export type CSVUploadInput = z.infer<typeof csvUploadSchema>;
```

### 3. File Upload Configuration
```typescript
// src/config/upload.config.ts
import { env } from './environment';
import path from 'path';

export const uploadConfig = {
  maxFileSize: env.MAX_FILE_SIZE,
  allowedMimeTypes: [
    'text/csv',
    'application/csv',
    'text/plain',
    'application/vnd.ms-excel',
  ],
  uploadDir: env.UPLOAD_DIR,
  tempDir: path.join(env.UPLOAD_DIR, 'temp'),
  processedDir: path.join(env.UPLOAD_DIR, 'processed'),
  errorDir: path.join(env.UPLOAD_DIR, 'errors'),
  csvDelimiter: ',',
  csvQuote: '"',
  csvEscape: '"',
  encoding: 'utf8',
  maxRows: 50000, // Maximum rows per CSV file
  chunkSize: 1000, // Process in chunks for memory efficiency
};

// CSV Type Mappings
export const csvTypeMappings = {
  active_listings: {
    expectedHeaders: [
      'Item number',
      'Title', 
      'Custom label (SKU)',
      'Available quantity',
      'Current price',
      'Sold quantity',
      'Start date',
      'End date',
      'eBay category 1 name'
    ],
    schema: 'activeListingSchema',
    tableName: 'listings',
  },
  sold_orders: {
    expectedHeaders: [
      'Order number',
      'Buyer username',
      'Item number',
      'Title',
      'Quantity',
      'Sale price',
      'Sale date',
      'Buyer name'
    ],
    schema: 'orderSchema',
    tableName: 'orders',
  },
  awaiting_shipment: {
    expectedHeaders: [
      'Order number',
      'Buyer username',
      'Item number',
      'Paid date',
      'Tracking number'
    ],
    schema: 'orderSchema',
    tableName: 'orders',
  },
  completed_orders: {
    expectedHeaders: [
      'Order number',
      'Item number',
      'Ship date',
      'Tracking number'
    ],
    schema: 'orderSchema',
    tableName: 'orders',
  }
} as const;
```

### 4. File Upload Middleware
```typescript
// src/middleware/file-upload.middleware.ts
import multer from 'multer';
import path from 'path';
import { uploadConfig } from '../config/upload.config';
import { Request } from 'express';

const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    cb(null, uploadConfig.tempDir);
  },
  filename: (req, file, cb) => {
    const timestamp = Date.now();
    const accountId = req.body.accountId || 'unknown';
    const csvType = req.body.csvType || 'unknown';
    const ext = path.extname(file.originalname);
    const filename = `${accountId}_${csvType}_${timestamp}${ext}`;
    cb(null, filename);
  },
});

const fileFilter = (req: Request, file: Express.Multer.File, cb: multer.FileFilterCallback) => {
  if (uploadConfig.allowedMimeTypes.includes(file.mimetype)) {
    cb(null, true);
  } else {
    cb(new Error(`Invalid file type. Allowed types: ${uploadConfig.allowedMimeTypes.join(', ')}`));
  }
};

export const uploadMiddleware = multer({
  storage,
  fileFilter,
  limits: {
    fileSize: uploadConfig.maxFileSize,
    files: 1, // Only allow one file at a time
  },
});

// CSV validation middleware
export const validateCSVStructure = async (
  req: Request,
  res: any,
  next: any
) => {
  try {
    if (!req.file) {
      return res.status(400).json({
        success: false,
        error: 'No file uploaded',
      });
    }

    const { csvType } = req.body;
    
    if (!csvType || !csvTypeMappings[csvType as keyof typeof csvTypeMappings]) {
      return res.status(400).json({
        success: false,
        error: 'Invalid CSV type specified',
      });
    }

    // Additional validation can be added here
    next();
  } catch (error) {
    res.status(400).json({
      success: false,
      error: error instanceof Error ? error.message : 'File validation failed',
    });
  }
};
```

### 5. CSV Parser Utility
```typescript
// src/utils/csv-parser.ts
import csv from 'csv-parser';
import fs from 'fs';
import { Readable } from 'stream';
import { uploadConfig } from '../config/upload.config';

export class CSVParser {
  static async parseFile(filePath: string): Promise<any[]> {
    return new Promise((resolve, reject) => {
      const results: any[] = [];
      let rowNumber = 0;
      
      fs.createReadStream(filePath)
        .pipe(csv({
          separator: uploadConfig.csvDelimiter,
          quote: uploadConfig.csvQuote,
          escape: uploadConfig.csvEscape,
        }))
        .on('data', (data) => {
          rowNumber++;
          if (rowNumber > uploadConfig.maxRows) {
            reject(new Error(`CSV file exceeds maximum allowed rows (${uploadConfig.maxRows})`));
            return;
          }
          results.push({ ...data, rowNumber });
        })
        .on('end', () => {
          resolve(results);
        })
        .on('error', (error) => {
          reject(error);
        });
    });
  }
  
  static async parseBuffer(buffer: Buffer): Promise<any[]> {
    return new Promise((resolve, reject) => {
      const results: any[] = [];
      let rowNumber = 0;
      
      const stream = Readable.from(buffer);
      
      stream
        .pipe(csv({
          separator: uploadConfig.csvDelimiter,
          quote: uploadConfig.csvQuote,
          escape: uploadConfig.csvEscape,
        }))
        .on('data', (data) => {
          rowNumber++;
          if (rowNumber > uploadConfig.maxRows) {
            reject(new Error(`CSV file exceeds maximum allowed rows (${uploadConfig.maxRows})`));
            return;
          }
          results.push({ ...data, rowNumber });
        })
        .on('end', () => {
          resolve(results);
        })
        .on('error', (error) => {
          reject(error);
        });
    });
  }
  
  static validateHeaders(data: any[], expectedHeaders: string[]): {
    isValid: boolean;
    missing: string[];
    extra: string[];
    actual: string[];
  } {
    if (data.length === 0) {
      return {
        isValid: false,
        missing: expectedHeaders,
        extra: [],
        actual: [],
      };
    }
    
    const actualHeaders = Object.keys(data[0]).filter(key => key !== 'rowNumber');
    const missing = expectedHeaders.filter(header => !actualHeaders.includes(header));
    const extra = actualHeaders.filter(header => !expectedHeaders.includes(header));
    
    return {
      isValid: missing.length === 0,
      missing,
      extra,
      actual: actualHeaders,
    };
  }
  
  static cleanCsvData(data: any[]): any[] {
    return data.map(row => {
      const cleanedRow: any = {};
      
      // Remove empty string values and convert to null
      for (const [key, value] of Object.entries(row)) {
        if (value === '' || value === undefined) {
          cleanedRow[key] = null;
        } else if (typeof value === 'string') {
          // Trim whitespace
          cleanedRow[key] = (value as string).trim();
        } else {
          cleanedRow[key] = value;
        }
      }
      
      return cleanedRow;
    });
  }
}
```

### 6. Data Transformer Utility
```typescript
// src/utils/data-transformer.ts
import { ActiveListingCSVInput, OrderCSVInput } from '../schemas/csv-schemas';
import { ActiveListingCSVRecord, OrderCSVRecord } from '../types/csv.types';

export class DataTransformer {
  static transformActiveListingRecord(input: ActiveListingCSVInput): ActiveListingCSVRecord {
    return {
      rowNumber: input.rowNumber,
      rawData: input,
      errors: input.errors || [],
      warnings: input.warnings || [],
      itemNumber: input['Item number'],
      title: input['Title'],
      variationDetails: input['Variation details'] || undefined,
      customLabelSKU: input['Custom label (SKU)'] || undefined,
      availableQuantity: input['Available quantity'],
      format: input['Format'],
      currency: input['Currency'],
      startPrice: input['Start price'],
      auctionBuyItNowPrice: input['Auction Buy It Now price'] || undefined,
      reservePrice: input['Reserve price'] || undefined,
      currentPrice: input['Current price'],
      soldQuantity: input['Sold quantity'] || 0,
      watchers: input['Watchers'] || 0,
      bids: input['Bids'] || undefined,
      startDate: input['Start date'],
      endDate: input['End date'],
      ebayCategoryName: input['eBay category 1 name'],
      ebayCategoryNumber: input['eBay category 1 number'],
      condition: input['Condition'],
      ebayProductId: input['eBay Product ID(ePID)']?.toString() || undefined,
      listingSite: input['Listing site'] || 'US',
      isbn: input['P:ISBN']?.toString() || undefined,
      upc: input['P:UPC']?.toString() || undefined,
      ean: input['P:EAN']?.toString() || undefined,
    };
  }
  
  static transformOrderRecord(input: OrderCSVInput): OrderCSVRecord {
    return {
      rowNumber: input.rowNumber,
      rawData: input,
      errors: input.errors || [],
      warnings: input.warnings || [],
      orderNumber: input['Order number'],
      buyerUsername: input['Buyer username'],
      buyerEmail: input['Buyer email'] || '',
      itemNumber: input['Item number'],
      title: input['Title'],
      sku: input['Custom label (SKU)'] || undefined,
      quantity: input['Quantity'],
      unitPrice: input['Sale price'],
      totalPrice: input['Total price'],
      orderDate: input['Sale date'],
      paymentDate: input['Paid date'],
      shippingDate: input['Ship date'],
      trackingNumber: input['Tracking number'] || undefined,
      shippingAddress: {
        name: input['Buyer name'],
        address1: input['Buyer address 1'],
        address2: input['Buyer address 2'] || undefined,
        city: input['Buyer city'],
        state: input['Buyer state'],
        zipCode: input['Buyer zip'],
        country: input['Buyer country'],
      },
    };
  }
  
  static validateRecord<T extends { errors: string[]; warnings: string[] }>(
    record: T,
    validationRules: ((record: T) => void)[]
  ): T {
    validationRules.forEach(rule => {
      try {
        rule(record);
      } catch (error) {
        if (error instanceof Error) {
          record.errors.push(error.message);
        }
      }
    });
    
    return record;
  }
  
  // Business logic validations
  static getActiveListingValidationRules() {
    return [
      (record: ActiveListingCSVRecord) => {
        if (record.availableQuantity < 0) {
          record.errors.push('Available quantity cannot be negative');
        }
      },
      (record: ActiveListingCSVRecord) => {
        if (record.currentPrice <= 0) {
          record.errors.push('Current price must be greater than 0');
        }
      },
      (record: ActiveListingCSVRecord) => {
        if (record.startDate >= record.endDate) {
          record.errors.push('Start date must be before end date');
        }
      },
      (record: ActiveListingCSVRecord) => {
        if (record.endDate < new Date()) {
          record.warnings.push('Listing has already ended');
        }
      },
      (record: ActiveListingCSVRecord) => {
        if (record.soldQuantity > 0 && record.availableQuantity === 0) {
          record.warnings.push('Item has sales but no available quantity');
        }
      },
    ];
  }
  
  static getOrderValidationRules() {
    return [
      (record: OrderCSVRecord) => {
        if (record.quantity <= 0) {
          record.errors.push('Quantity must be greater than 0');
        }
      },
      (record: OrderCSVRecord) => {
        if (record.unitPrice <= 0) {
          record.errors.push('Unit price must be greater than 0');
        }
      },
      (record: OrderCSVRecord) => {
        const expectedTotal = record.unitPrice * record.quantity;
        if (Math.abs(record.totalPrice - expectedTotal) > 0.01) {
          record.warnings.push(`Total price mismatch: expected ${expectedTotal}, got ${record.totalPrice}`);
        }
      },
      (record: OrderCSVRecord) => {
        if (!record.buyerEmail || !record.buyerEmail.includes('@')) {
          record.warnings.push('Buyer email is missing or invalid');
        }
      },
    ];
  }
}
```

### 7. CSV Processing Service
```typescript
// src/services/csv-processor.service.ts
import { prisma } from '../config/database';
import { CSVParser } from '../utils/csv-parser';
import { DataTransformer } from '../utils/data-transformer';
import { activeListingSchema, orderSchema } from '../schemas/csv-schemas';
import {
  CSVType,
  CSVProcessingResult,
  ProcessingError,
  ActiveListingCSVRecord,
  OrderCSVRecord,
} from '../types/csv.types';
import { csvTypeMappings, uploadConfig } from '../config/upload.config';
import fs from 'fs';
import path from 'path';

export class CSVProcessorService {
  
  async processCSVFile(
    filePath: string,
    csvType: CSVType,
    accountId: number,
    userId: number,
    options: { replaceExisting?: boolean; dryRun?: boolean } = {}
  ): Promise<CSVProcessingResult> {
    const startTime = Date.now();
    
    // Initialize sync history record
    const syncRecord = await prisma.syncHistory.create({
      data: {
        accountId,
        syncType: csvType,
        fileName: path.basename(filePath),
        fileSize: fs.statSync(filePath).size,
        syncStatus: 'processing',
      },
    });
    
    try {
      // Parse CSV file
      const rawData = await CSVParser.parseFile(filePath);
      const cleanedData = CSVParser.cleanCsvData(rawData);
      
      // Validate CSV structure
      const typeMapping = csvTypeMappings[csvType];
      const headerValidation = CSVParser.validateHeaders(cleanedData, typeMapping.expectedHeaders);
      
      if (!headerValidation.isValid) {
        throw new Error(`Invalid CSV structure. Missing headers: ${headerValidation.missing.join(', ')}`);
      }
      
      // Process records based on type
      let result: CSVProcessingResult;
      
      switch (csvType) {
        case 'active_listings':
          result = await this.processActiveListings(cleanedData, accountId, options);
          break;
        case 'sold_orders':
        case 'awaiting_shipment':
        case 'completed_orders':
          result = await this.processOrders(cleanedData, accountId, csvType, options);
          break;
        default:
          throw new Error(`Unsupported CSV type: ${csvType}`);
      }
      
      // Update sync history
      const processingTime = Math.round((Date.now() - startTime) / 1000);
      await prisma.syncHistory.update({
        where: { id: syncRecord.id },
        data: {
          recordsProcessed: result.totalRecords,
          recordsSuccess: result.processedRecords,
          recordsFailed: result.invalidRecords,
          syncStatus: result.success ? 'completed' : 'failed',
          completedAt: new Date(),
          processingTime,
          errorMessage: result.success ? null : result.errors[0]?.message,
        },
      });
      
      // Move file to appropriate directory
      const targetDir = result.success ? uploadConfig.processedDir : uploadConfig.errorDir;
      const targetPath = path.join(targetDir, path.basename(filePath));
      fs.renameSync(filePath, targetPath);
      
      return result;
      
    } catch (error) {
      // Update sync history with error
      await prisma.syncHistory.update({
        where: { id: syncRecord.id },
        data: {
          syncStatus: 'failed',
          errorMessage: error instanceof Error ? error.message : 'Unknown error',
          completedAt: new Date(),
          processingTime: Math.round((Date.now() - startTime) / 1000),
        },
      });
      
      // Move file to error directory
      const errorPath = path.join(uploadConfig.errorDir, path.basename(filePath));
      fs.renameSync(filePath, errorPath);
      
      throw error;
    }
  }
  
  private async processActiveListings(
    data: any[],
    accountId: number,
    options: { replaceExisting?: boolean; dryRun?: boolean }
  ): Promise<CSVProcessingResult> {
    const result: CSVProcessingResult = {
      success: true,
      totalRecords: data.length,
      validRecords: 0,
      invalidRecords: 0,
      processedRecords: 0,
      errors: [],
      warnings: [],
      duplicates: 0,
      summary: { created: 0, updated: 0, skipped: 0, failed: 0 },
    };
    
    const validationRules = DataTransformer.getActiveListingValidationRules();
    const processedRecords: ActiveListingCSVRecord[] = [];
    
    // Process records in chunks
    for (let i = 0; i < data.length; i += uploadConfig.chunkSize) {
      const chunk = data.slice(i, i + uploadConfig.chunkSize);
      
      for (const rawRecord of chunk) {
        try {
          // Validate against schema
          const validatedData = activeListingSchema.parse(rawRecord);
          
          // Transform to business object
          const record = DataTransformer.transformActiveListingRecord(validatedData);
          
          // Apply business validations
          DataTransformer.validateRecord(record, validationRules);
          
          if (record.errors.length === 0) {
            result.validRecords++;
            processedRecords.push(record);
          } else {
            result.invalidRecords++;
            result.errors.push({
              row: record.rowNumber,
              message: record.errors.join('; '),
              severity: 'error',
              data: record,
            });
          }
          
          // Add warnings to result
          if (record.warnings.length > 0) {
            result.warnings.push({
              row: record.rowNumber,
              message: record.warnings.join('; '),
              data: record,
            });
          }
          
        } catch (error) {
          result.invalidRecords++;
          result.errors.push({
            row: rawRecord.rowNumber,
            message: error instanceof Error ? error.message : 'Validation failed',
            severity: 'error',
            data: rawRecord,
          });
        }
      }
    }
    
    // Save to database if not dry run
    if (!options.dryRun) {
      const dbResults = await this.saveActiveListings(processedRecords, accountId, options.replaceExisting);
      result.summary = dbResults.summary;
      result.processedRecords = dbResults.processed;
      result.duplicates = dbResults.duplicates;
    } else {
      result.processedRecords = result.validRecords;
    }
    
    result.success = result.errors.length === 0;
    return result;
  }
  
  private async processOrders(
    data: any[],
    accountId: number,
    csvType: CSVType,
    options: { replaceExisting?: boolean; dryRun?: boolean }
  ): Promise<CSVProcessingResult> {
    const result: CSVProcessingResult = {
      success: true,
      totalRecords: data.length,
      validRecords: 0,
      invalidRecords: 0,
      processedRecords: 0,
      errors: [],
      warnings: [],
      duplicates: 0,
      summary: { created: 0, updated: 0, skipped: 0, failed: 0 },
    };
    
    const validationRules = DataTransformer.getOrderValidationRules();
    const processedRecords: OrderCSVRecord[] = [];
    
    // Process records in chunks
    for (let i = 0; i < data.length; i += uploadConfig.chunkSize) {
      const chunk = data.slice(i, i + uploadConfig.chunkSize);
      
      for (const rawRecord of chunk) {
        try {
          // Validate against schema
          const validatedData = orderSchema.parse(rawRecord);
          
          // Transform to business object
          const record = DataTransformer.transformOrderRecord(validatedData);
          
          // Apply business validations
          DataTransformer.validateRecord(record, validationRules);
          
          if (record.errors.length === 0) {
            result.validRecords++;
            processedRecords.push(record);
          } else {
            result.invalidRecords++;
            result.errors.push({
              row: record.rowNumber,
              message: record.errors.join('; '),
              severity: 'error',
              data: record,
            });
          }
          
          // Add warnings to result
          if (record.warnings.length > 0) {
            result.warnings.push({
              row: record.rowNumber,
              message: record.warnings.join('; '),
              data: record,
            });
          }
          
        } catch (error) {
          result.invalidRecords++;
          result.errors.push({
            row: rawRecord.rowNumber,
            message: error instanceof Error ? error.message : 'Validation failed',
            severity: 'error',
            data: rawRecord,
          });
        }
      }
    }
    
    // Save to database if not dry run
    if (!options.dryRun) {
      const dbResults = await this.saveOrders(processedRecords, accountId, options.replaceExisting);
      result.summary = dbResults.summary;
      result.processedRecords = dbResults.processed;
      result.duplicates = dbResults.duplicates;
    } else {
      result.processedRecords = result.validRecords;
    }
    
    result.success = result.errors.length === 0;
    return result;
  }
  
  private async saveActiveListings(
    records: ActiveListingCSVRecord[],
    accountId: number,
    replaceExisting: boolean = false
  ) {
    const summary = { created: 0, updated: 0, skipped: 0, failed: 0 };
    let processed = 0;
    let duplicates = 0;
    
    // If replace existing, delete all current listings for this account
    if (replaceExisting) {
      await prisma.listing.deleteMany({
        where: { ebayAccountId: accountId },
      });
    }
    
    for (const record of records) {
      try {
        // Check if listing already exists
        const existingListing = await prisma.listing.findFirst({
          where: {
            itemNumber: record.itemNumber,
            ebayAccountId: accountId,
          },
        });
        
        const listingData = {
          itemNumber: record.itemNumber,
          title: record.title,
          sku: record.customLabelSKU,
          availableQuantity: record.availableQuantity,
          soldQuantity: record.soldQuantity,
          currentPrice: record.currentPrice,
          startPrice: record.startPrice,
          format: record.format,
          condition: record.condition,
          categoryName: record.ebayCategoryName,
          startDate: record.startDate,
          endDate: record.endDate,
          listingStatus: record.availableQuantity > 0 ? 'active' : 'sold',
          watchers: record.watchers,
          ebayProductId: record.ebayProductId,
          isbn: record.isbn,
          upc: record.upc,
          ean: record.ean,
        };
        
        if (existingListing) {
          if (!replaceExisting) {
            duplicates++;
            summary.skipped++;
            continue;
          }
          
          await prisma.listing.update({
            where: { id: existingListing.id },
            data: listingData,
          });
          summary.updated++;
        } else {
          await prisma.listing.create({
            data: {
              ...listingData,
              ebayAccountId: accountId,
            },
          });
          summary.created++;
        }
        
        processed++;
        
      } catch (error) {
        summary.failed++;
      }
    }
    
    return { summary, processed, duplicates };
  }
  
  private async saveOrders(
    records: OrderCSVRecord[],
    accountId: number,
    replaceExisting: boolean = false
  ) {
    const summary = { created: 0, updated: 0, skipped: 0, failed: 0 };
    let processed = 0;
    let duplicates = 0;
    
    for (const record of records) {
      try {
        // Check if order already exists
        const existingOrder = await prisma.order.findFirst({
          where: {
            ebayOrderId: record.orderNumber,
            ebayAccountId: accountId,
          },
        });
        
        const orderData = {
          ebayOrderId: record.orderNumber,
          buyerUsername: record.buyerUsername,
          buyerEmail: record.buyerEmail,
          totalAmount: record.totalPrice,
          currency: 'USD', // Default currency
          orderDate: record.orderDate,
          paymentStatus: record.paymentDate ? 'paid' : 'pending',
          shippingStatus: record.shippingDate ? 'shipped' : 'pending',
          trackingNumber: record.trackingNumber,
          shippingAddress: JSON.stringify(record.shippingAddress),
        };
        
        if (existingOrder) {
          if (!replaceExisting) {
            duplicates++;
            summary.skipped++;
            continue;
          }
          
          await prisma.order.update({
            where: { id: existingOrder.id },
            data: orderData,
          });
          summary.updated++;
        } else {
          const newOrder = await prisma.order.create({
            data: {
              ...orderData,
              ebayAccountId: accountId,
            },
          });
          
          // Create order item
          await prisma.orderItem.create({
            data: {
              orderId: newOrder.id,
              itemNumber: record.itemNumber,
              title: record.title,
              sku: record.sku,
              quantity: record.quantity,
              unitPrice: record.unitPrice,
              totalPrice: record.totalPrice,
              variationDetails: record.rawData['Variation details'] || null,
            },
          });
          
          summary.created++;
        }
        
        processed++;
        
      } catch (error) {
        summary.failed++;
      }
    }
    
    return { summary, processed, duplicates };
  }
}
```

### 8. Upload Controller
```typescript
// src/controllers/upload.controller.ts
import { Request, Response } from 'express';
import { CSVProcessorService } from '../services/csv-processor.service';
import { csvUploadSchema } from '../schemas/csv-schemas';
import { ApiResponse } from '../types/common.types';
import fs from 'fs';

const csvProcessor = new CSVProcessorService();

export class UploadController {
  async uploadCSV(req: Request, res: Response<ApiResponse>) {
    try {
      if (!req.file) {
        return res.status(400).json({
          success: false,
          error: 'No file uploaded',
        });
      }
      
      // Validate request body
      const validatedData = csvUploadSchema.parse(req.body);
      const userId = req.user?.userId;
      
      if (!userId) {
        return res.status(401).json({
          success: false,
          error: 'User not authenticated',
        });
      }
      
      // Check if user has access to this account
      if (req.user?.role !== 'super_admin' && !req.user?.accountIds.includes(validatedData.accountId)) {
        return res.status(403).json({
          success: false,
          error: 'Access denied to this account',
        });
      }
      
      // Process CSV file
      const result = await csvProcessor.processCSVFile(
        req.file.path,
        validatedData.csvType,
        validatedData.accountId,
        userId,
        {
          replaceExisting: validatedData.replaceExisting,
          dryRun: validatedData.dryRun,
        }
      );
      
      res.json({
        success: result.success,
        data: {
          processingResult: result,
          fileInfo: {
            filename: req.file.filename,
            originalName: req.file.originalname,
            size: req.file.size,
            csvType: validatedData.csvType,
            accountId: validatedData.accountId,
          },
        },
        message: `CSV processing ${result.success ? 'completed' : 'failed'}. Processed ${result.processedRecords} of ${result.totalRecords} records.`,
      });
      
    } catch (error) {
      // Clean up uploaded file on error
      if (req.file && fs.existsSync(req.file.path)) {
        fs.unlinkSync(req.file.path);
      }
      
      res.status(500).json({
        success: false,
        error: error instanceof Error ? error.message : 'CSV processing failed',
      });
    }
  }
  
  async getSyncHistory(req: Request, res: Response<ApiResponse>) {
    try {
      const accountId = parseInt(req.params.accountId);
      const page = parseInt(req.query.page as string) || 1;
      const limit = parseInt(req.query.limit as string) || 20;
      const syncType = req.query.syncType as string;
      
      // Check account access
      if (req.user?.role !== 'super_admin' && !req.user?.accountIds.includes(accountId)) {
        return res.status(403).json({
          success: false,
          error: 'Access denied to this account',
        });
      }
      
      const skip = (page - 1) * limit;
      const where: any = { accountId };
      
      if (syncType) {
        where.syncType = syncType;
      }
      
      const [syncHistory, total] = await Promise.all([
        prisma.syncHistory.findMany({
          where,
          skip,
          take: limit,
          orderBy: { startedAt: 'desc' },
          include: {
            account: {
              select: {
                accountName: true,
              },
            },
          },
        }),
        prisma.syncHistory.count({ where }),
      ]);
      
      res.json({
        success: true,
        data: syncHistory,
        meta: {
          page,
          limit,
          total,
          totalPages: Math.ceil(total / limit),
        },
      });
      
    } catch (error) {
      res.status(500).json({
        success: false,
        error: error instanceof Error ? error.message : 'Failed to get sync history',
      });
    }
  }
}
```

### 9. Upload Routes
```typescript
// src/routes/upload.routes.ts
import { Router } from 'express';
import { UploadController } from '../controllers/upload.controller';
import { authenticate, checkAccountAccess } from '../middleware/auth.middleware';
import { uploadMiddleware, validateCSVStructure } from '../middleware/file-upload.middleware';

const router = Router();
const uploadController = new UploadController();

// All routes require authentication
router.use(authenticate);

// CSV upload endpoint
router.post(
  '/csv',
  uploadMiddleware.single('csvFile'),
  validateCSVStructure,
  uploadController.uploadCSV.bind(uploadController)
);

// Sync history
router.get(
  '/sync-history/:accountId',
  checkAccountAccess,
  uploadController.getSyncHistory.bind(uploadController)
);

export default router;
```

### 10. Database Schema Updates
```typescript
// Update prisma/schema.prisma to add new models
model Listing {
  id                Int           @id @default(autoincrement())
  ebayAccountId     Int           @map("ebay_account_id")
  itemNumber        BigInt        @map("item_number")
  title             String        @db.VarChar(255)
  sku               String?       @db.VarChar(100)
  availableQuantity Int           @map("available_quantity")
  soldQuantity      Int           @default(0) @map("sold_quantity")
  currentPrice      Decimal       @map("current_price") @db.Decimal(10, 2)
  startPrice        Decimal       @map("start_price") @db.Decimal(10, 2)
  format            String        @db.VarChar(20)
  condition         String        @db.VarChar(50)
  categoryName      String        @map("category_name") @db.VarChar(100)
  startDate         DateTime      @map("start_date")
  endDate           DateTime      @map("end_date")
  listingStatus     String        @default("active") @map("listing_status") @db.VarChar(20)
  watchers          Int           @default(0)
  ebayProductId     String?       @map("ebay_product_id") @db.VarChar(50)
  isbn              String?       @db.VarChar(20)
  upc               String?       @db.VarChar(20)
  ean               String?       @db.VarChar(20)
  createdAt         DateTime      @default(now()) @map("created_at")
  updatedAt         DateTime      @updatedAt @map("updated_at")

  // Relations
  account           EbayAccount   @relation(fields: [ebayAccountId], references: [id], onDelete: Cascade)
  orderItems        OrderItem[]

  @@unique([itemNumber, ebayAccountId])
  @@map("listings")
}

model Order {
  id              Int        @id @default(autoincrement())
  ebayAccountId   Int        @map("ebay_account_id")
  ebayOrderId     String     @map("ebay_order_id") @db.VarChar(50)
  buyerUsername   String     @map("buyer_username") @db.VarChar(100)
  buyerEmail      String     @map("buyer_email") @db.VarChar(255)
  totalAmount     Decimal    @map("total_amount") @db.Decimal(10, 2)
  currency        String     @default("USD") @db.VarChar(3)
  orderDate       DateTime   @map("order_date")
  paymentStatus   String     @default("pending") @map("payment_status") @db.VarChar(20)
  shippingStatus  String     @default("pending") @map("shipping_status") @db.VarChar(20)
  trackingNumber  String?    @map("tracking_number") @db.VarChar(100)
  shippingAddress Json       @map("shipping_address")
  createdAt       DateTime   @default(now()) @map("created_at")
  updatedAt       DateTime   @updatedAt @map("updated_at")

  // Relations
  account         EbayAccount @relation(fields: [ebayAccountId], references: [id], onDelete: Cascade)
  orderItems      OrderItem[]

  @@unique([ebayOrderId, ebayAccountId])
  @@map("orders")
}

model OrderItem {
  id               Int     @id @default(autoincrement())
  orderId          Int     @map("order_id")
  itemNumber       BigInt  @map("item_number")
  title            String  @db.VarChar(255)
  sku              String? @db.VarChar(100)
  quantity         Int
  unitPrice        Decimal @map("unit_price") @db.Decimal(10, 2)
  totalPrice       Decimal @map("total_price") @db.Decimal(10, 2)
  variationDetails String? @map("variation_details") @db.Text

  // Relations
  order            Order    @relation(fields: [orderId], references: [id], onDelete: Cascade)
  listing          Listing? @relation(fields: [itemNumber, accountId], references: [itemNumber, ebayAccountId])

  @@map("order_items")
}
```

## Success Criteria

1. ✅ CSV parsing and validation working
2. ✅ File upload with security checks
3. ✅ Data transformation pipeline
4. ✅ Active listings processing
5. ✅ Order processing for multiple CSV types
6. ✅ Error handling and reporting
7. ✅ Sync history tracking
8. ✅ Database storage with relationships
9. ✅ Bulk processing with memory efficiency
10. ✅ Duplicate detection and handling

## Next Steps
- Plan 4: Order Management Module with status updates
- Plan 5: Listing Management with bulk operations