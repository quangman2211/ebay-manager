# Plan 7: Customer Management & Communication Module

## Objective
Build comprehensive customer management and communication system with Gmail integration, eBay message processing, customer segmentation, communication templates, and automated response capabilities.

## Dependencies
- Plan 1: Database Setup & Foundation completed
- Plan 2: Authentication & User Management APIs completed  
- Plan 3: CSV Processing Engine completed
- Plan 4: Order Management Module completed
- Plan 5: Listing Management Module completed
- Plan 6: Product & Supplier Management Module completed

## File Structure Updates
```
src/
├── services/
│   ├── customer.service.ts (enhanced from Plan 4)
│   ├── communication.service.ts
│   ├── gmail.service.ts
│   ├── ebay-message.service.ts
│   ├── template.service.ts
│   └── customer-segmentation.service.ts
├── controllers/
│   ├── customer.controller.ts
│   ├── communication.controller.ts
│   └── template.controller.ts
├── routes/
│   ├── customer.routes.ts
│   └── communication.routes.ts
├── schemas/
│   ├── customer.schema.ts
│   ├── communication.schema.ts
│   └── template.schema.ts
├── types/
│   ├── communication.types.ts
│   └── customer.types.ts
├── utils/
│   ├── email-parser.ts
│   ├── message-classifier.ts
│   └── customer-analyzer.ts
├── middleware/
│   └── gmail-auth.middleware.ts
└── jobs/
    ├── gmail-sync.job.ts
    ├── message-processing.job.ts
    └── customer-analysis.job.ts
```

## Implementation Files

### 1. Communication Type Definitions
```typescript
// src/types/communication.types.ts

export interface CommunicationFilter {
  customerId?: number;
  accountId?: number;
  messageType?: MessageType[];
  direction?: MessageDirection[];
  status?: MessageStatus[];
  dateRange?: {
    start: Date;
    end: Date;
  };
  hasResponse?: boolean;
  priority?: MessagePriority[];
  category?: MessageCategory[];
  search?: string;
}

export type MessageType = 'email' | 'ebay_message' | 'system_note' | 'phone_call' | 'live_chat';
export type MessageDirection = 'inbound' | 'outbound';
export type MessageStatus = 'unread' | 'read' | 'replied' | 'archived' | 'flagged' | 'spam';
export type MessagePriority = 'low' | 'normal' | 'high' | 'urgent';
export type MessageCategory = 'inquiry' | 'complaint' | 'compliment' | 'return_request' | 'shipping_issue' | 'payment_issue' | 'technical_support' | 'general';

export interface CommunicationMessage {
  id: number;
  customerId?: number;
  accountId: number;
  messageType: MessageType;
  direction: MessageDirection;
  subject: string;
  content: string;
  htmlContent?: string;
  priority: MessagePriority;
  category: MessageCategory;
  status: MessageStatus;
  threadId?: string;
  externalId?: string; // Gmail message ID or eBay message ID
  attachments?: MessageAttachment[];
  metadata?: any; // Additional message-specific data
  sentAt: Date;
  readAt?: Date;
  repliedAt?: Date;
  assignedTo?: number;
  tags?: string[];
  createdAt: Date;
  updatedAt: Date;
}

export interface MessageAttachment {
  id: string;
  filename: string;
  contentType: string;
  size: number;
  url?: string;
}

export interface GmailSyncConfig {
  accountId: number;
  gmailAddress: string;
  refreshToken: string;
  accessToken: string;
  lastSyncAt?: Date;
  syncLabels?: string[];
  autoCategories: boolean;
  autoResponses: boolean;
}

export interface EbayMessageImport {
  accountId: number;
  csvFile: string;
  importType: 'full' | 'incremental';
  dateFrom?: Date;
  dateTo?: Date;
}

export interface MessageTemplate {
  id: number;
  name: string;
  category: MessageCategory;
  subject: string;
  content: string;
  variables?: TemplateVariable[];
  isActive: boolean;
  accountIds?: number[];
  usageCount: number;
  createdBy: number;
  createdAt: Date;
  updatedAt: Date;
}

export interface TemplateVariable {
  name: string;
  type: 'text' | 'number' | 'date' | 'customer_field' | 'order_field';
  description: string;
  defaultValue?: string;
  required: boolean;
}

export interface AutoResponseRule {
  id: number;
  name: string;
  accountIds: number[];
  triggers: {
    keywords?: string[];
    category?: MessageCategory;
    timeOfDay?: { start: string; end: string };
    dayOfWeek?: number[];
  };
  conditions: {
    firstMessage: boolean;
    customerType?: string[];
    orderValue?: { min?: number; max?: number };
  };
  response: {
    templateId: number;
    delay?: number; // minutes
    variables?: { [key: string]: string };
  };
  isActive: boolean;
  priority: number;
  createdBy: number;
}

export interface CommunicationMetrics {
  totalMessages: number;
  unreadMessages: number;
  avgResponseTime: number; // minutes
  responseRate: number; // percentage
  customerSatisfactionScore?: number;
  messagesByCategory: { [category: string]: number };
  messagesByPriority: { [priority: string]: number };
  dailyVolume: Array<{
    date: string;
    inbound: number;
    outbound: number;
  }>;
  topCustomers: Array<{
    customerId: number;
    customerName: string;
    messageCount: number;
  }>;
}

export interface CustomerInteraction {
  customerId: number;
  totalMessages: number;
  lastContactDate: Date;
  avgResponseTime: number;
  satisfactionScore?: number;
  preferredChannel: MessageType;
  communicationHistory: Array<{
    date: Date;
    type: MessageType;
    category: MessageCategory;
    resolved: boolean;
  }>;
  openIssues: number;
  escalatedIssues: number;
}
```

### 2. Enhanced Customer Types
```typescript
// src/types/customer.types.ts (enhanced from Plan 4)

export interface CustomerProfile extends Customer {
  communicationPreferences: {
    preferredChannel: MessageType;
    language: string;
    timeZone: string;
    optOutEmail: boolean;
    optOutSms: boolean;
  };
  behaviorMetrics: {
    avgOrderValue: number;
    orderFrequency: number;
    lastActivityDate: Date;
    lifetimeValue: number;
    returnRate: number;
    communicationScore: number;
  };
  riskFactors: {
    disputeHistory: number;
    returnFrequency: number;
    paymentIssues: number;
    communicationTone: 'positive' | 'neutral' | 'negative';
    riskLevel: 'low' | 'medium' | 'high';
  };
  interactions: CustomerInteraction;
  tags: string[];
  notes: CustomerNote[];
}

export interface CustomerNote {
  id: number;
  customerId: number;
  content: string;
  noteType: 'general' | 'warning' | 'compliment' | 'issue';
  isVisible: boolean;
  createdBy: number;
  createdAt: Date;
}

export interface CustomerSegmentRule {
  id: number;
  name: string;
  description: string;
  conditions: {
    totalOrders?: { min?: number; max?: number };
    totalSpent?: { min?: number; max?: number };
    lastOrderDays?: number;
    communicationScore?: { min?: number; max?: number };
    riskLevel?: string[];
    tags?: string[];
  };
  actions: {
    assignTags?: string[];
    setType?: string;
    setRisk?: string;
    notifyUsers?: number[];
  };
  isActive: boolean;
  priority: number;
  lastRunAt?: Date;
}

export interface CustomerCampaign {
  id: number;
  name: string;
  description: string;
  targetSegments: string[];
  messageTemplate: string;
  scheduleType: 'immediate' | 'scheduled' | 'recurring';
  scheduleDate?: Date;
  recurringPattern?: string;
  status: 'draft' | 'scheduled' | 'running' | 'completed' | 'paused';
  metrics: {
    targetCount: number;
    sentCount: number;
    deliveredCount: number;
    openRate: number;
    responseRate: number;
  };
  createdBy: number;
  createdAt: Date;
}
```

### 3. Communication Schemas
```typescript
// src/schemas/communication.schema.ts
import { z } from 'zod';

export const communicationFilterSchema = z.object({
  customerId: z.number().positive().optional(),
  accountId: z.number().positive().optional(),
  messageType: z.array(z.enum(['email', 'ebay_message', 'system_note', 'phone_call', 'live_chat'])).optional(),
  direction: z.array(z.enum(['inbound', 'outbound'])).optional(),
  status: z.array(z.enum(['unread', 'read', 'replied', 'archived', 'flagged', 'spam'])).optional(),
  dateRange: z.object({
    start: z.string().datetime(),
    end: z.string().datetime(),
  }).optional(),
  hasResponse: z.boolean().optional(),
  priority: z.array(z.enum(['low', 'normal', 'high', 'urgent'])).optional(),
  category: z.array(z.enum(['inquiry', 'complaint', 'compliment', 'return_request', 'shipping_issue', 'payment_issue', 'technical_support', 'general'])).optional(),
  search: z.string().max(255).optional(),
});

export const sendMessageSchema = z.object({
  customerId: z.number().positive().optional(),
  accountId: z.number().positive(),
  messageType: z.enum(['email', 'ebay_message', 'system_note']),
  subject: z.string().min(1).max(255),
  content: z.string().min(1).max(10000),
  htmlContent: z.string().max(20000).optional(),
  priority: z.enum(['low', 'normal', 'high', 'urgent']).default('normal'),
  category: z.enum(['inquiry', 'complaint', 'compliment', 'return_request', 'shipping_issue', 'payment_issue', 'technical_support', 'general']).default('general'),
  templateId: z.number().positive().optional(),
  templateVariables: z.record(z.string(), z.string()).optional(),
  scheduledAt: z.string().datetime().optional(),
});

export const createTemplateSchema = z.object({
  name: z.string().min(1).max(255),
  category: z.enum(['inquiry', 'complaint', 'compliment', 'return_request', 'shipping_issue', 'payment_issue', 'technical_support', 'general']),
  subject: z.string().min(1).max(255),
  content: z.string().min(1).max(10000),
  variables: z.array(z.object({
    name: z.string().min(1).max(50),
    type: z.enum(['text', 'number', 'date', 'customer_field', 'order_field']),
    description: z.string().max(255),
    defaultValue: z.string().optional(),
    required: z.boolean().default(false),
  })).optional(),
  accountIds: z.array(z.number().positive()).optional(),
});

export const updateTemplateSchema = createTemplateSchema.partial();

export const gmailSyncConfigSchema = z.object({
  gmailAddress: z.string().email(),
  refreshToken: z.string().min(1),
  syncLabels: z.array(z.string()).default(['INBOX']),
  autoCategories: z.boolean().default(true),
  autoResponses: z.boolean().default(false),
});

export const importEbayMessagesSchema = z.object({
  importType: z.enum(['full', 'incremental']).default('incremental'),
  dateFrom: z.string().datetime().optional(),
  dateTo: z.string().datetime().optional(),
});

export const autoResponseRuleSchema = z.object({
  name: z.string().min(1).max(255),
  accountIds: z.array(z.number().positive()),
  triggers: z.object({
    keywords: z.array(z.string().max(50)).optional(),
    category: z.enum(['inquiry', 'complaint', 'compliment', 'return_request', 'shipping_issue', 'payment_issue', 'technical_support', 'general']).optional(),
    timeOfDay: z.object({
      start: z.string().regex(/^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$/),
      end: z.string().regex(/^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$/),
    }).optional(),
    dayOfWeek: z.array(z.number().min(0).max(6)).optional(),
  }),
  conditions: z.object({
    firstMessage: z.boolean().default(false),
    customerType: z.array(z.string()).optional(),
    orderValue: z.object({
      min: z.number().min(0).optional(),
      max: z.number().min(0).optional(),
    }).optional(),
  }),
  response: z.object({
    templateId: z.number().positive(),
    delay: z.number().min(0).max(1440).optional(), // max 24 hours
    variables: z.record(z.string(), z.string()).optional(),
  }),
  priority: z.number().min(1).max(100).default(50),
});

export const customerNoteSchema = z.object({
  content: z.string().min(1).max(2000),
  noteType: z.enum(['general', 'warning', 'compliment', 'issue']).default('general'),
  isVisible: z.boolean().default(true),
});

export type CommunicationFilterInput = z.infer<typeof communicationFilterSchema>;
export type SendMessageInput = z.infer<typeof sendMessageSchema>;
export type CreateTemplateInput = z.infer<typeof createTemplateSchema>;
export type UpdateTemplateInput = z.infer<typeof updateTemplateSchema>;
export type GmailSyncConfigInput = z.infer<typeof gmailSyncConfigSchema>;
export type ImportEbayMessagesInput = z.infer<typeof importEbayMessagesSchema>;
export type AutoResponseRuleInput = z.infer<typeof autoResponseRuleSchema>;
export type CustomerNoteInput = z.infer<typeof customerNoteSchema>;
```

### 4. Gmail Service
```typescript
// src/services/gmail.service.ts
import { google } from 'googleapis';
import { prisma } from '../config/database';
import { MessageClassifier } from '../utils/message-classifier';
import { EmailParser } from '../utils/email-parser';

export class GmailService {
  private oauth2Client = new google.auth.OAuth2(
    process.env.GOOGLE_CLIENT_ID,
    process.env.GOOGLE_CLIENT_SECRET,
    process.env.GOOGLE_REDIRECT_URI
  );

  async setupGmailSync(accountId: number, config: any, userId: number) {
    // Save Gmail configuration
    const gmailConfig = await prisma.gmailSyncConfig.upsert({
      where: { accountId },
      update: {
        gmailAddress: config.gmailAddress,
        refreshToken: config.refreshToken,
        accessToken: config.accessToken,
        syncLabels: JSON.stringify(config.syncLabels || ['INBOX']),
        autoCategories: config.autoCategories,
        autoResponses: config.autoResponses,
        updatedAt: new Date(),
      },
      create: {
        accountId,
        gmailAddress: config.gmailAddress,
        refreshToken: config.refreshToken,
        accessToken: config.accessToken,
        syncLabels: JSON.stringify(config.syncLabels || ['INBOX']),
        autoCategories: config.autoCategories,
        autoResponses: config.autoResponses,
      },
    });

    return gmailConfig;
  }

  async syncGmailMessages(accountId: number, fullSync: boolean = false) {
    const config = await prisma.gmailSyncConfig.findUnique({
      where: { accountId },
    });

    if (!config) {
      throw new Error('Gmail sync not configured for this account');
    }

    // Set up OAuth2 client
    this.oauth2Client.setCredentials({
      refresh_token: config.refreshToken,
      access_token: config.accessToken,
    });

    const gmail = google.gmail({ version: 'v1', auth: this.oauth2Client });
    const syncLabels = JSON.parse(config.syncLabels || '["INBOX"]');
    
    let query = '';
    if (!fullSync && config.lastSyncAt) {
      const syncDate = config.lastSyncAt.toISOString().split('T')[0];
      query = `after:${syncDate}`;
    }

    // Add eBay-related filters
    query += ' (from:ebay.com OR from:@ebay.com OR from:members.ebay.com OR subject:ebay)';

    const results = {
      processed: 0,
      imported: 0,
      errors: [] as string[],
    };

    try {
      // Get message list
      const messageList = await gmail.users.messages.list({
        userId: 'me',
        q: query,
        maxResults: 500,
      });

      if (!messageList.data.messages) {
        return results;
      }

      // Process messages in batches
      const batchSize = 10;
      for (let i = 0; i < messageList.data.messages.length; i += batchSize) {
        const batch = messageList.data.messages.slice(i, i + batchSize);
        
        const promises = batch.map(async (msg) => {
          try {
            await this.processGmailMessage(accountId, gmail, msg.id!, config.autoCategories);
            results.imported++;
          } catch (error) {
            results.errors.push(`Message ${msg.id}: ${error instanceof Error ? error.message : 'Unknown error'}`);
          }
          results.processed++;
        });

        await Promise.all(promises);
      }

      // Update last sync time
      await prisma.gmailSyncConfig.update({
        where: { accountId },
        data: { lastSyncAt: new Date() },
      });

    } catch (error) {
      throw new Error(`Gmail sync failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }

    return results;
  }

  private async processGmailMessage(
    accountId: number,
    gmail: any,
    messageId: string,
    autoCategories: boolean
  ) {
    // Check if message already exists
    const existingMessage = await prisma.communicationMessage.findFirst({
      where: {
        externalId: messageId,
        messageType: 'email',
      },
    });

    if (existingMessage) {
      return; // Skip if already processed
    }

    // Get full message details
    const message = await gmail.users.messages.get({
      userId: 'me',
      id: messageId,
      format: 'full',
    });

    const headers = message.data.payload.headers;
    const subject = headers.find((h: any) => h.name === 'Subject')?.value || 'No Subject';
    const fromHeader = headers.find((h: any) => h.name === 'From')?.value || '';
    const toHeader = headers.find((h: any) => h.name === 'To')?.value || '';
    const dateHeader = headers.find((h: any) => h.name === 'Date')?.value;

    // Parse email content
    const { textContent, htmlContent } = EmailParser.extractContent(message.data.payload);
    
    // Determine message direction
    const direction = this.determineDirection(fromHeader, toHeader, accountId);
    
    // Extract customer information
    let customerId: number | undefined;
    if (direction === 'inbound') {
      customerId = await this.findOrCreateCustomer(fromHeader, accountId);
    }

    // Auto-categorize if enabled
    let category = 'general';
    let priority = 'normal';
    if (autoCategories) {
      const classification = MessageClassifier.classifyMessage(subject, textContent);
      category = classification.category;
      priority = classification.priority;
    }

    // Create communication message
    const communicationMessage = await prisma.communicationMessage.create({
      data: {
        accountId,
        customerId,
        messageType: 'email',
        direction,
        subject,
        content: textContent,
        htmlContent,
        priority,
        category,
        status: direction === 'inbound' ? 'unread' : 'read',
        externalId: messageId,
        threadId: message.data.threadId,
        sentAt: dateHeader ? new Date(dateHeader) : new Date(),
        metadata: JSON.stringify({
          from: fromHeader,
          to: toHeader,
          gmailLabels: message.data.labelIds,
        }),
      },
    });

    return communicationMessage;
  }

  private determineDirection(fromHeader: string, toHeader: string, accountId: number): 'inbound' | 'outbound' {
    // This would check against known account email addresses
    // For now, simplified logic
    if (fromHeader.includes('ebay.com') || fromHeader.includes('@members.ebay.com')) {
      return 'inbound';
    }
    return 'inbound'; // Default to inbound for customer emails
  }

  private async findOrCreateCustomer(fromHeader: string, accountId: number): Promise<number | undefined> {
    const emailMatch = fromHeader.match(/<(.+@.+)>/) || fromHeader.match(/(.+@.+)/);
    if (!emailMatch) return undefined;

    const email = emailMatch[1].trim().toLowerCase();
    
    // Try to find existing customer
    let customer = await prisma.customer.findFirst({
      where: {
        OR: [
          { email },
          { ebayUsername: email.split('@')[0] },
        ],
      },
    });

    if (!customer) {
      // Create new customer from email
      const name = fromHeader.replace(/<.*>/, '').trim() || email.split('@')[0];
      customer = await prisma.customer.create({
        data: {
          ebayUsername: email.split('@')[0],
          email,
          fullName: name,
          customerType: 'new',
          firstOrderDate: new Date(),
          lastOrderDate: new Date(),
          totalOrders: 0,
          totalSpent: 0,
        },
      });
    }

    return customer.id;
  }

  async sendEmailResponse(
    messageId: number,
    replyContent: string,
    userId: number
  ) {
    const originalMessage = await prisma.communicationMessage.findUnique({
      where: { id: messageId },
      include: {
        account: {
          include: {
            gmailConfig: true,
          },
        },
        customer: true,
      },
    });

    if (!originalMessage || !originalMessage.account.gmailConfig) {
      throw new Error('Cannot send reply - Gmail not configured');
    }

    // Set up OAuth2 client
    this.oauth2Client.setCredentials({
      refresh_token: originalMessage.account.gmailConfig.refreshToken,
      access_token: originalMessage.account.gmailConfig.accessToken,
    });

    const gmail = google.gmail({ version: 'v1', auth: this.oauth2Client });

    // Prepare email
    const subject = originalMessage.subject.startsWith('Re:') 
      ? originalMessage.subject 
      : `Re: ${originalMessage.subject}`;
    
    const metadata = JSON.parse(originalMessage.metadata || '{}');
    const toAddress = metadata.from;

    const emailContent = [
      'Content-Type: text/plain; charset="UTF-8"\n',
      'MIME-Version: 1.0\n',
      `To: ${toAddress}\n`,
      `Subject: ${subject}\n`,
      `In-Reply-To: ${originalMessage.externalId}\n`,
      `References: ${originalMessage.externalId}\n`,
      '\n',
      replyContent
    ].join('');

    const encodedMessage = Buffer.from(emailContent).toString('base64');

    // Send email
    const sentMessage = await gmail.users.messages.send({
      userId: 'me',
      requestBody: {
        raw: encodedMessage,
        threadId: originalMessage.threadId,
      },
    });

    // Create outbound communication record
    const outboundMessage = await prisma.communicationMessage.create({
      data: {
        accountId: originalMessage.accountId,
        customerId: originalMessage.customerId,
        messageType: 'email',
        direction: 'outbound',
        subject,
        content: replyContent,
        priority: originalMessage.priority,
        category: originalMessage.category,
        status: 'read',
        externalId: sentMessage.data.id,
        threadId: originalMessage.threadId,
        sentAt: new Date(),
        metadata: JSON.stringify({
          replyTo: messageId,
          to: toAddress,
        }),
      },
    });

    // Mark original message as replied
    await prisma.communicationMessage.update({
      where: { id: messageId },
      data: { 
        status: 'replied',
        repliedAt: new Date(),
      },
    });

    return outboundMessage;
  }
}
```

### 5. eBay Message Service
```typescript
// src/services/ebay-message.service.ts
import { prisma } from '../config/database';
import { CSVParser } from '../utils/csv-parser';
import { MessageClassifier } from '../utils/message-classifier';

export class EbayMessageService {
  async importMessagesFromCSV(
    filePath: string,
    accountId: number,
    importType: 'full' | 'incremental' = 'incremental',
    dateRange?: { start: Date; end: Date }
  ) {
    const results = {
      processed: 0,
      imported: 0,
      updated: 0,
      errors: [] as string[],
    };

    try {
      // Parse CSV file
      const rawData = await CSVParser.parseFile(filePath);
      
      // Expected eBay message CSV structure
      const expectedHeaders = [
        'Message ID',
        'Date',
        'From',
        'To', 
        'Subject',
        'Message',
        'Item ID',
        'Item Title',
        'Status'
      ];

      const headerValidation = CSVParser.validateHeaders(rawData, expectedHeaders);
      if (!headerValidation.isValid) {
        throw new Error(`Invalid CSV structure. Missing headers: ${headerValidation.missing.join(', ')}`);
      }

      // Process messages
      for (const row of rawData) {
        try {
          results.processed++;
          
          const messageDate = new Date(row['Date']);
          
          // Apply date range filter if specified
          if (dateRange) {
            if (messageDate < dateRange.start || messageDate > dateRange.end) {
              continue;
            }
          }

          const messageId = row['Message ID'];
          const fromUser = row['From'];
          const toUser = row['To'];
          const subject = row['Subject'] || 'No Subject';
          const content = row['Message'] || '';
          const itemId = row['Item ID'];
          const itemTitle = row['Item Title'];
          const status = row['Status']?.toLowerCase() || 'active';

          // Check if message already exists
          const existingMessage = await prisma.communicationMessage.findFirst({
            where: {
              externalId: messageId.toString(),
              messageType: 'ebay_message',
            },
          });

          if (existingMessage && importType === 'incremental') {
            // Update existing message if needed
            if (existingMessage.status !== status) {
              await prisma.communicationMessage.update({
                where: { id: existingMessage.id },
                data: { status },
              });
              results.updated++;
            }
            continue;
          }

          // Determine message direction
          const direction = await this.determineMessageDirection(fromUser, toUser, accountId);
          
          // Find or create customer
          let customerId: number | undefined;
          if (direction === 'inbound') {
            customerId = await this.findOrCreateCustomerFromEbay(fromUser, accountId);
          }

          // Classify message
          const classification = MessageClassifier.classifyMessage(subject, content);

          // Create communication message
          await prisma.communicationMessage.create({
            data: {
              accountId,
              customerId,
              messageType: 'ebay_message',
              direction,
              subject,
              content,
              priority: classification.priority,
              category: classification.category,
              status: direction === 'inbound' ? 'unread' : 'read',
              externalId: messageId.toString(),
              sentAt: messageDate,
              metadata: JSON.stringify({
                from: fromUser,
                to: toUser,
                itemId,
                itemTitle,
                ebayStatus: status,
              }),
            },
          });

          results.imported++;

        } catch (error) {
          results.errors.push(`Row ${results.processed}: ${error instanceof Error ? error.message : 'Unknown error'}`);
        }
      }

    } catch (error) {
      throw new Error(`eBay message import failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }

    return results;
  }

  private async determineMessageDirection(
    fromUser: string,
    toUser: string,
    accountId: number
  ): Promise<'inbound' | 'outbound'> {
    // Get account's eBay username
    const account = await prisma.ebayAccount.findUnique({
      where: { id: accountId },
      select: { ebayUsername: true, accountEmail: true },
    });

    if (account) {
      // Check if message is from the account owner
      if (fromUser === account.ebayUsername || fromUser === account.accountEmail) {
        return 'outbound';
      }
      // Check if message is to the account owner
      if (toUser === account.ebayUsername || toUser === account.accountEmail) {
        return 'inbound';
      }
    }

    // Default to inbound for customer messages
    return 'inbound';
  }

  private async findOrCreateCustomerFromEbay(ebayUsername: string, accountId: number): Promise<number | undefined> {
    if (!ebayUsername || ebayUsername.trim() === '') return undefined;

    // Try to find existing customer by eBay username
    let customer = await prisma.customer.findFirst({
      where: {
        OR: [
          { ebayUsername: ebayUsername.trim() },
          { email: { contains: ebayUsername.trim() } },
        ],
      },
    });

    if (!customer) {
      // Create new customer from eBay username
      customer = await prisma.customer.create({
        data: {
          ebayUsername: ebayUsername.trim(),
          email: `${ebayUsername.trim()}@ebay.placeholder`,
          fullName: ebayUsername.trim(),
          customerType: 'new',
          firstOrderDate: new Date(),
          lastOrderDate: new Date(),
          totalOrders: 0,
          totalSpent: 0,
        },
      });
    }

    return customer.id;
  }

  async getEbayMessagesByItem(itemId: string, accountId: number) {
    const messages = await prisma.communicationMessage.findMany({
      where: {
        accountId,
        messageType: 'ebay_message',
        metadata: {
          path: ['itemId'],
          equals: itemId,
        },
      },
      include: {
        customer: {
          select: {
            ebayUsername: true,
            fullName: true,
            customerType: true,
          },
        },
      },
      orderBy: { sentAt: 'asc' },
    });

    return messages.map(message => ({
      ...message,
      metadata: JSON.parse(message.metadata || '{}'),
    }));
  }

  async getCustomerMessageThread(customerId: number, accountId: number) {
    const messages = await prisma.communicationMessage.findMany({
      where: {
        accountId,
        customerId,
        messageType: { in: ['ebay_message', 'email'] },
      },
      orderBy: { sentAt: 'desc' },
      take: 50,
    });

    return messages.map(message => ({
      ...message,
      metadata: JSON.parse(message.metadata || '{}'),
    }));
  }

  async markMessageAsRead(messageId: number, userId: number) {
    const message = await prisma.communicationMessage.update({
      where: { id: messageId },
      data: {
        status: 'read',
        readAt: new Date(),
      },
    });

    return message;
  }

  async flagMessage(messageId: number, flag: boolean, userId: number) {
    const status = flag ? 'flagged' : 'read';
    
    const message = await prisma.communicationMessage.update({
      where: { id: messageId },
      data: { status },
    });

    return message;
  }

  async archiveMessage(messageId: number, userId: number) {
    const message = await prisma.communicationMessage.update({
      where: { id: messageId },
      data: { status: 'archived' },
    });

    return message;
  }

  async getMessageStatistics(accountId?: number, dateRange?: { start: Date; end: Date }) {
    const where: any = {};
    
    if (accountId) {
      where.accountId = accountId;
    }
    
    if (dateRange) {
      where.sentAt = {
        gte: dateRange.start,
        lte: dateRange.end,
      };
    }

    const [
      totalMessages,
      unreadMessages,
      messagesByType,
      messagesByCategory,
      messagesByStatus,
      responseTimeStats,
    ] = await Promise.all([
      prisma.communicationMessage.count({ where }),
      prisma.communicationMessage.count({ where: { ...where, status: 'unread' } }),
      prisma.communicationMessage.groupBy({
        by: ['messageType'],
        where,
        _count: { id: true },
      }),
      prisma.communicationMessage.groupBy({
        by: ['category'],
        where,
        _count: { id: true },
      }),
      prisma.communicationMessage.groupBy({
        by: ['status'],
        where,
        _count: { id: true },
      }),
      prisma.communicationMessage.findMany({
        where: {
          ...where,
          repliedAt: { not: null },
          sentAt: { not: null },
        },
        select: {
          sentAt: true,
          repliedAt: true,
        },
      }),
    ]);

    // Calculate average response time
    const responseTimes = responseTimeStats
      .filter(msg => msg.repliedAt && msg.sentAt)
      .map(msg => (msg.repliedAt!.getTime() - msg.sentAt.getTime()) / (1000 * 60)); // minutes

    const avgResponseTime = responseTimes.length > 0 
      ? responseTimes.reduce((sum, time) => sum + time, 0) / responseTimes.length 
      : 0;

    return {
      totalMessages,
      unreadMessages,
      avgResponseTime: Math.round(avgResponseTime),
      responseRate: totalMessages > 0 ? (responseTimes.length / totalMessages) * 100 : 0,
      messagesByType: messagesByType.reduce((acc, item) => ({
        ...acc,
        [item.messageType]: item._count.id,
      }), {}),
      messagesByCategory: messagesByCategory.reduce((acc, item) => ({
        ...acc,
        [item.category]: item._count.id,
      }), {}),
      messagesByStatus: messagesByStatus.reduce((acc, item) => ({
        ...acc,
        [item.status]: item._count.id,
      }), {}),
    };
  }
}
```

### 6. Message Template Service
```typescript
// src/services/template.service.ts
import { prisma } from '../config/database';
import { CreateTemplateInput, UpdateTemplateInput } from '../schemas/communication.schema';
import { PaginationParams, FilterParams } from '../types/common.types';

export class TemplateService {
  async createTemplate(data: CreateTemplateInput, createdBy: number) {
    const template = await prisma.messageTemplate.create({
      data: {
        name: data.name,
        category: data.category,
        subject: data.subject,
        content: data.content,
        variables: data.variables ? JSON.stringify(data.variables) : null,
        accountIds: data.accountIds ? JSON.stringify(data.accountIds) : null,
        isActive: true,
        usageCount: 0,
        createdBy,
      },
    });

    return {
      ...template,
      variables: template.variables ? JSON.parse(template.variables) : [],
      accountIds: template.accountIds ? JSON.parse(template.accountIds) : [],
    };
  }

  async getTemplates(
    pagination: PaginationParams,
    filters: FilterParams & { category?: string; isActive?: boolean },
    accountIds?: number[]
  ) {
    const { page = 1, limit = 20, sortBy = 'name', sortOrder = 'asc' } = pagination;
    const { search, category, isActive } = filters;
    
    const skip = (page - 1) * limit;
    const where: any = {};

    if (search) {
      where.OR = [
        { name: { contains: search, mode: 'insensitive' } },
        { subject: { contains: search, mode: 'insensitive' } },
        { content: { contains: search, mode: 'insensitive' } },
      ];
    }

    if (category) {
      where.category = category;
    }

    if (isActive !== undefined) {
      where.isActive = isActive;
    }

    // Filter by account access if specified
    if (accountIds && accountIds.length > 0) {
      where.OR = [
        { accountIds: null }, // Global templates
        ...accountIds.map(id => ({
          accountIds: {
            path: '$',
            array_contains: id,
          },
        })),
      ];
    }

    const [templates, total] = await Promise.all([
      prisma.messageTemplate.findMany({
        where,
        skip,
        take: limit,
        orderBy: { [sortBy]: sortOrder },
        include: {
          createdByUser: {
            select: {
              username: true,
              fullName: true,
            },
          },
        },
      }),
      prisma.messageTemplate.count({ where }),
    ]);

    return {
      templates: templates.map(template => ({
        ...template,
        variables: template.variables ? JSON.parse(template.variables) : [],
        accountIds: template.accountIds ? JSON.parse(template.accountIds) : [],
      })),
      pagination: {
        page,
        limit,
        total,
        totalPages: Math.ceil(total / limit),
      },
    };
  }

  async getTemplateById(templateId: number) {
    const template = await prisma.messageTemplate.findUnique({
      where: { id: templateId },
      include: {
        createdByUser: {
          select: {
            username: true,
            fullName: true,
          },
        },
      },
    });

    if (!template) {
      throw new Error('Template not found');
    }

    return {
      ...template,
      variables: template.variables ? JSON.parse(template.variables) : [],
      accountIds: template.accountIds ? JSON.parse(template.accountIds) : [],
    };
  }

  async updateTemplate(templateId: number, data: UpdateTemplateInput) {
    const updateData: any = { ...data };
    
    if (data.variables) {
      updateData.variables = JSON.stringify(data.variables);
    }
    
    if (data.accountIds) {
      updateData.accountIds = JSON.stringify(data.accountIds);
    }

    const template = await prisma.messageTemplate.update({
      where: { id: templateId },
      data: updateData,
    });

    return {
      ...template,
      variables: template.variables ? JSON.parse(template.variables) : [],
      accountIds: template.accountIds ? JSON.parse(template.accountIds) : [],
    };
  }

  async renderTemplate(templateId: number, variables: { [key: string]: any }) {
    const template = await this.getTemplateById(templateId);
    
    let renderedSubject = template.subject;
    let renderedContent = template.content;

    // Replace variables in subject and content
    Object.entries(variables).forEach(([key, value]) => {
      const placeholder = `{{${key}}}`;
      renderedSubject = renderedSubject.replace(new RegExp(placeholder, 'g'), String(value));
      renderedContent = renderedContent.replace(new RegExp(placeholder, 'g'), String(value));
    });

    // Increment usage count
    await prisma.messageTemplate.update({
      where: { id: templateId },
      data: {
        usageCount: { increment: 1 },
      },
    });

    return {
      subject: renderedSubject,
      content: renderedContent,
      template,
    };
  }

  async duplicateTemplate(templateId: number, newName: string, createdBy: number) {
    const originalTemplate = await this.getTemplateById(templateId);
    
    const duplicateData = {
      name: newName,
      category: originalTemplate.category,
      subject: originalTemplate.subject,
      content: originalTemplate.content,
      variables: originalTemplate.variables,
      accountIds: originalTemplate.accountIds,
    };

    return this.createTemplate(duplicateData, createdBy);
  }

  async getTemplatesByCategory(category?: string, accountIds?: number[]) {
    const where: any = { isActive: true };
    
    if (category) {
      where.category = category;
    }

    if (accountIds && accountIds.length > 0) {
      where.OR = [
        { accountIds: null }, // Global templates
        ...accountIds.map(id => ({
          accountIds: {
            path: '$',
            array_contains: id,
          },
        })),
      ];
    }

    const templates = await prisma.messageTemplate.findMany({
      where,
      select: {
        id: true,
        name: true,
        category: true,
        subject: true,
        usageCount: true,
        variables: true,
      },
      orderBy: [
        { category: 'asc' },
        { usageCount: 'desc' },
        { name: 'asc' },
      ],
    });

    return templates.map(template => ({
      ...template,
      variables: template.variables ? JSON.parse(template.variables) : [],
    }));
  }

  async getTemplateStatistics() {
    const [
      totalTemplates,
      activeTemplates,
      categoryBreakdown,
      mostUsedTemplates,
      unusedTemplates,
    ] = await Promise.all([
      prisma.messageTemplate.count(),
      prisma.messageTemplate.count({ where: { isActive: true } }),
      prisma.messageTemplate.groupBy({
        by: ['category'],
        _count: { id: true },
      }),
      prisma.messageTemplate.findMany({
        where: { isActive: true },
        select: {
          id: true,
          name: true,
          category: true,
          usageCount: true,
        },
        orderBy: { usageCount: 'desc' },
        take: 10,
      }),
      prisma.messageTemplate.count({
        where: {
          isActive: true,
          usageCount: 0,
        },
      }),
    ]);

    return {
      totalTemplates,
      activeTemplates,
      inactiveTemplates: totalTemplates - activeTemplates,
      unusedTemplates,
      categoryBreakdown: categoryBreakdown.reduce((acc, item) => ({
        ...acc,
        [item.category]: item._count.id,
      }), {}),
      mostUsedTemplates,
    };
  }

  async toggleTemplateStatus(templateId: number) {
    const template = await prisma.messageTemplate.findUnique({
      where: { id: templateId },
      select: { isActive: true },
    });

    if (!template) {
      throw new Error('Template not found');
    }

    const updatedTemplate = await prisma.messageTemplate.update({
      where: { id: templateId },
      data: { isActive: !template.isActive },
    });

    return {
      ...updatedTemplate,
      variables: updatedTemplate.variables ? JSON.parse(updatedTemplate.variables) : [],
      accountIds: updatedTemplate.accountIds ? JSON.parse(updatedTemplate.accountIds) : [],
    };
  }

  async deleteTemplate(templateId: number) {
    // Check if template is being used in auto-response rules
    const usageCount = await prisma.autoResponseRule.count({
      where: {
        'response.templateId': templateId,
      },
    });

    if (usageCount > 0) {
      throw new Error('Cannot delete template that is being used in auto-response rules');
    }

    await prisma.messageTemplate.delete({
      where: { id: templateId },
    });

    return { success: true };
  }
}
```

### 7. Communication Controller
```typescript
// src/controllers/communication.controller.ts
import { Request, Response } from 'express';
import { CommunicationService } from '../services/communication.service';
import { GmailService } from '../services/gmail.service';
import { EbayMessageService } from '../services/ebay-message.service';
import { TemplateService } from '../services/template.service';
import {
  communicationFilterSchema,
  sendMessageSchema,
  gmailSyncConfigSchema,
  importEbayMessagesSchema,
} from '../schemas/communication.schema';
import { ApiResponse } from '../types/common.types';

const communicationService = new CommunicationService();
const gmailService = new GmailService();
const ebayMessageService = new EbayMessageService();
const templateService = new TemplateService();

export class CommunicationController {
  async getMessages(req: Request, res: Response<ApiResponse>) {
    try {
      const page = parseInt(req.query.page as string) || 1;
      const limit = parseInt(req.query.limit as string) || 20;
      const sortBy = req.query.sortBy as string || 'sentAt';
      const sortOrder = (req.query.sortOrder as 'asc' | 'desc') || 'desc';
      
      const filters = communicationFilterSchema.parse({
        customerId: req.query.customerId ? parseInt(req.query.customerId as string) : undefined,
        accountId: req.query.accountId ? parseInt(req.query.accountId as string) : undefined,
        messageType: req.query.messageType ? (req.query.messageType as string).split(',') : undefined,
        direction: req.query.direction ? (req.query.direction as string).split(',') : undefined,
        status: req.query.status ? (req.query.status as string).split(',') : undefined,
        dateRange: req.query.startDate && req.query.endDate ? {
          start: new Date(req.query.startDate as string).toISOString(),
          end: new Date(req.query.endDate as string).toISOString(),
        } : undefined,
        hasResponse: req.query.hasResponse === 'true' ? true : req.query.hasResponse === 'false' ? false : undefined,
        priority: req.query.priority ? (req.query.priority as string).split(',') : undefined,
        category: req.query.category ? (req.query.category as string).split(',') : undefined,
        search: req.query.search as string,
      });
      
      const result = await communicationService.getMessages(
        { page, limit, sortBy, sortOrder },
        filters,
        req.user?.accountIds
      );
      
      res.json({
        success: true,
        data: result.messages,
        meta: result.pagination,
      });
    } catch (error) {
      res.status(500).json({
        success: false,
        error: error instanceof Error ? error.message : 'Failed to get messages',
      });
    }
  }

  async getMessageById(req: Request, res: Response<ApiResponse>) {
    try {
      const messageId = parseInt(req.params.id);
      const message = await communicationService.getMessageById(messageId);
      
      // Check if user has access to this message's account
      if (req.user?.role !== 'super_admin' && !req.user?.accountIds.includes(message.accountId)) {
        return res.status(403).json({
          success: false,
          error: 'Access denied to this message',
        });
      }
      
      res.json({
        success: true,
        data: message,
      });
    } catch (error) {
      res.status(404).json({
        success: false,
        error: error instanceof Error ? error.message : 'Message not found',
      });
    }
  }

  async sendMessage(req: Request, res: Response<ApiResponse>) {
    try {
      const validatedData = sendMessageSchema.parse(req.body);
      const userId = req.user?.userId;
      
      if (!userId) {
        return res.status(401).json({
          success: false,
          error: 'User not authenticated',
        });
      }
      
      // Check account access
      if (req.user?.role !== 'super_admin' && !req.user?.accountIds.includes(validatedData.accountId)) {
        return res.status(403).json({
          success: false,
          error: 'Access denied to this account',
        });
      }
      
      const message = await communicationService.sendMessage(validatedData, userId);
      
      res.status(201).json({
        success: true,
        data: message,
        message: 'Message sent successfully',
      });
    } catch (error) {
      res.status(400).json({
        success: false,
        error: error instanceof Error ? error.message : 'Failed to send message',
      });
    }
  }

  async replyToMessage(req: Request, res: Response<ApiResponse>) {
    try {
      const messageId = parseInt(req.params.id);
      const { content, templateId, templateVariables } = req.body;
      const userId = req.user?.userId;
      
      if (!userId) {
        return res.status(401).json({
          success: false,
          error: 'User not authenticated',
        });
      }
      
      const reply = await communicationService.replyToMessage(
        messageId,
        content,
        userId,
        templateId,
        templateVariables
      );
      
      res.json({
        success: true,
        data: reply,
        message: 'Reply sent successfully',
      });
    } catch (error) {
      res.status(400).json({
        success: false,
        error: error instanceof Error ? error.message : 'Failed to send reply',
      });
    }
  }

  async setupGmailSync(req: Request, res: Response<ApiResponse>) {
    try {
      const accountId = parseInt(req.params.accountId);
      const validatedData = gmailSyncConfigSchema.parse(req.body);
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
      
      const config = await gmailService.setupGmailSync(accountId, validatedData, userId);
      
      res.json({
        success: true,
        data: config,
        message: 'Gmail sync configured successfully',
      });
    } catch (error) {
      res.status(400).json({
        success: false,
        error: error instanceof Error ? error.message : 'Failed to setup Gmail sync',
      });
    }
  }

  async syncGmailMessages(req: Request, res: Response<ApiResponse>) {
    try {
      const accountId = parseInt(req.params.accountId);
      const fullSync = req.query.fullSync === 'true';
      
      // Check account access
      if (req.user?.role !== 'super_admin' && !req.user?.accountIds.includes(accountId)) {
        return res.status(403).json({
          success: false,
          error: 'Access denied to this account',
        });
      }
      
      const result = await gmailService.syncGmailMessages(accountId, fullSync);
      
      res.json({
        success: true,
        data: result,
        message: `Gmail sync completed. Processed: ${result.processed}, Imported: ${result.imported}`,
      });
    } catch (error) {
      res.status(500).json({
        success: false,
        error: error instanceof Error ? error.message : 'Gmail sync failed',
      });
    }
  }

  async importEbayMessages(req: Request, res: Response<ApiResponse>) {
    try {
      const accountId = parseInt(req.params.accountId);
      const validatedData = importEbayMessagesSchema.parse(req.body);
      
      if (!req.file) {
        return res.status(400).json({
          success: false,
          error: 'CSV file is required',
        });
      }
      
      // Check account access
      if (req.user?.role !== 'super_admin' && !req.user?.accountIds.includes(accountId)) {
        return res.status(403).json({
          success: false,
          error: 'Access denied to this account',
        });
      }
      
      const dateRange = validatedData.dateFrom && validatedData.dateTo ? {
        start: new Date(validatedData.dateFrom),
        end: new Date(validatedData.dateTo),
      } : undefined;
      
      const result = await ebayMessageService.importMessagesFromCSV(
        req.file.path,
        accountId,
        validatedData.importType,
        dateRange
      );
      
      res.json({
        success: true,
        data: result,
        message: `eBay messages imported. Processed: ${result.processed}, Imported: ${result.imported}`,
      });
    } catch (error) {
      res.status(500).json({
        success: false,
        error: error instanceof Error ? error.message : 'eBay message import failed',
      });
    }
  }

  async getCommunicationMetrics(req: Request, res: Response<ApiResponse>) {
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
      
      const metrics = await communicationService.getCommunicationMetrics(accountId, dateRange);
      
      res.json({
        success: true,
        data: metrics,
      });
    } catch (error) {
      res.status(500).json({
        success: false,
        error: error instanceof Error ? error.message : 'Failed to get communication metrics',
      });
    }
  }

  async markMessageAsRead(req: Request, res: Response<ApiResponse>) {
    try {
      const messageId = parseInt(req.params.id);
      const userId = req.user?.userId;
      
      if (!userId) {
        return res.status(401).json({
          success: false,
          error: 'User not authenticated',
        });
      }
      
      const message = await ebayMessageService.markMessageAsRead(messageId, userId);
      
      res.json({
        success: true,
        data: message,
        message: 'Message marked as read',
      });
    } catch (error) {
      res.status(400).json({
        success: false,
        error: error instanceof Error ? error.message : 'Failed to mark message as read',
      });
    }
  }

  async getCustomerCommunications(req: Request, res: Response<ApiResponse>) {
    try {
      const customerId = parseInt(req.params.customerId);
      const accountId = parseInt(req.params.accountId);
      
      // Check account access
      if (req.user?.role !== 'super_admin' && !req.user?.accountIds.includes(accountId)) {
        return res.status(403).json({
          success: false,
          error: 'Access denied to this account',
        });
      }
      
      const messages = await ebayMessageService.getCustomerMessageThread(customerId, accountId);
      
      res.json({
        success: true,
        data: messages,
        meta: { count: messages.length, customerId, accountId },
      });
    } catch (error) {
      res.status(500).json({
        success: false,
        error: error instanceof Error ? error.message : 'Failed to get customer communications',
      });
    }
  }
}
```

### 8. Database Schema Updates
```prisma
// Add to existing schema in prisma/schema.prisma

model GmailSyncConfig {
  id              Int      @id @default(autoincrement())
  accountId       Int      @unique @map("account_id")
  gmailAddress    String   @map("gmail_address") @db.VarChar(255)
  refreshToken    String   @map("refresh_token") @db.Text
  accessToken     String   @map("access_token") @db.Text
  lastSyncAt      DateTime? @map("last_sync_at")
  syncLabels      String   @default("[\"INBOX\"]") @map("sync_labels") @db.Text // JSON
  autoCategories  Boolean  @default(true) @map("auto_categories")
  autoResponses   Boolean  @default(false) @map("auto_responses")
  createdAt       DateTime @default(now()) @map("created_at")
  updatedAt       DateTime @updatedAt @map("updated_at")

  // Relations
  account         EbayAccount @relation(fields: [accountId], references: [id], onDelete: Cascade)

  @@map("gmail_sync_configs")
}

model CommunicationMessage {
  id              Int      @id @default(autoincrement())
  customerId      Int?     @map("customer_id")
  accountId       Int      @map("account_id")
  messageType     String   @map("message_type") @db.VarChar(20)
  direction       String   @db.VarChar(10)
  subject         String   @db.VarChar(500)
  content         String   @db.Text
  htmlContent     String?  @map("html_content") @db.Text
  priority        String   @default("normal") @db.VarChar(10)
  category        String   @default("general") @db.VarChar(30)
  status          String   @default("unread") @db.VarChar(20)
  threadId        String?  @map("thread_id") @db.VarChar(100)
  externalId      String?  @map("external_id") @db.VarChar(100)
  attachments     String?  @db.Text // JSON array
  metadata        String?  @db.Text // JSON
  sentAt          DateTime @map("sent_at")
  readAt          DateTime? @map("read_at")
  repliedAt       DateTime? @map("replied_at")
  assignedTo      Int?     @map("assigned_to")
  tags            String?  @db.Text // JSON array
  createdAt       DateTime @default(now()) @map("created_at")
  updatedAt       DateTime @updatedAt @map("updated_at")

  // Relations
  customer        Customer? @relation(fields: [customerId], references: [id])
  account         EbayAccount @relation(fields: [accountId], references: [id], onDelete: Cascade)
  assignedUser    User?     @relation(fields: [assignedTo], references: [id])

  @@index([accountId, status])
  @@index([customerId])
  @@index([externalId])
  @@map("communication_messages")
}

model MessageTemplate {
  id              Int      @id @default(autoincrement())
  name            String   @db.VarChar(255)
  category        String   @db.VarChar(30)
  subject         String   @db.VarChar(500)
  content         String   @db.Text
  variables       String?  @db.Text // JSON array
  isActive        Boolean  @default(true) @map("is_active")
  accountIds      String?  @map("account_ids") @db.Text // JSON array, null = global
  usageCount      Int      @default(0) @map("usage_count")
  createdBy       Int      @map("created_by")
  createdAt       DateTime @default(now()) @map("created_at")
  updatedAt       DateTime @updatedAt @map("updated_at")

  // Relations
  createdByUser   User     @relation(fields: [createdBy], references: [id])

  @@map("message_templates")
}

model AutoResponseRule {
  id              Int      @id @default(autoincrement())
  name            String   @db.VarChar(255)
  accountIds      String   @map("account_ids") @db.Text // JSON array
  triggers        String   @db.Text // JSON
  conditions      String   @db.Text // JSON
  response        String   @db.Text // JSON
  isActive        Boolean  @default(true) @map("is_active")
  priority        Int      @default(50)
  lastTriggered   DateTime? @map("last_triggered")
  triggerCount    Int      @default(0) @map("trigger_count")
  createdBy       Int      @map("created_by")
  createdAt       DateTime @default(now()) @map("created_at")
  updatedAt       DateTime @updatedAt @map("updated_at")

  // Relations
  createdByUser   User     @relation(fields: [createdBy], references: [id])

  @@map("auto_response_rules")
}

model CustomerNote {
  id              Int      @id @default(autoincrement())
  customerId      Int      @map("customer_id")
  content         String   @db.Text
  noteType        String   @default("general") @map("note_type") @db.VarChar(20)
  isVisible       Boolean  @default(true) @map("is_visible")
  createdBy       Int      @map("created_by")
  createdAt       DateTime @default(now()) @map("created_at")

  // Relations
  customer        Customer @relation(fields: [customerId], references: [id], onDelete: Cascade)
  createdByUser   User     @relation(fields: [createdBy], references: [id])

  @@map("customer_notes")
}

// Update existing Customer model
model Customer {
  id                    Int      @id @default(autoincrement())
  ebayUsername          String   @unique @map("ebay_username") @db.VarChar(100)
  email                 String   @map("email") @db.VarChar(255)
  fullName              String?  @map("full_name") @db.VarChar(255)
  phone                 String?  @db.VarChar(50)
  address               Json?
  customerType          String   @default("new") @map("customer_type") @db.VarChar(20)
  firstOrderDate        DateTime @map("first_order_date")
  lastOrderDate         DateTime @map("last_order_date")
  totalOrders           Int      @default(0) @map("total_orders")
  totalSpent            Decimal  @default(0) @map("total_spent") @db.Decimal(10, 2)
  communicationScore    Int      @default(5) @map("communication_score") @db.SmallInt
  riskLevel             String   @default("low") @map("risk_level") @db.VarChar(10)
  preferredChannel      String?  @map("preferred_channel") @db.VarChar(20)
  language              String   @default("en") @db.VarChar(5)
  timeZone              String?  @map("time_zone") @db.VarChar(50)
  tags                  String?  @db.Text // JSON array
  notes                 String?
  isActive              Boolean  @default(true) @map("is_active")
  createdAt             DateTime @default(now()) @map("created_at")
  updatedAt             DateTime @updatedAt @map("updated_at")

  // Relations
  segments              CustomerSegment[]
  communicationMessages CommunicationMessage[]
  customerNotes         CustomerNote[]

  @@map("customers")
}

// Update existing models to include new relations
model EbayAccount {
  // ... existing fields ...
  
  // Relations
  user                  User     @relation(fields: [userId], references: [id], onDelete: Cascade)
  accountPermissions    UserAccountPermission[]
  syncHistory           SyncHistory[]
  listings              Listing[]
  orders                Order[]
  draftListings         DraftListing[]
  gmailConfig           GmailSyncConfig?
  communicationMessages CommunicationMessage[]

  @@map("ebay_accounts")
}

model User {
  // ... existing fields ...
  
  // Relations
  ebayAccounts          EbayAccount[]
  accountPermissions    UserAccountPermission[]
  assignedPermissions   UserAccountPermission[] @relation("AssignedBy")
  orderStatusUpdates    OrderStatusHistory[]
  draftListings         DraftListing[]
  listingHistory        ListingHistory[]
  suppliers             Supplier[]
  products              Product[]
  stockAdjustments      StockAdjustment[]
  stockReservations     StockReservation[]
  purchaseOrders        PurchaseOrder[]
  messageTemplates      MessageTemplate[]
  autoResponseRules     AutoResponseRule[]
  customerNotes         CustomerNote[]
  assignedMessages      CommunicationMessage[]

  @@map("users")
}
```

### 9. API Routes
```typescript
// src/routes/communication.routes.ts
import { Router } from 'express';
import { CommunicationController } from '../controllers/communication.controller';
import { TemplateController } from '../controllers/template.controller';
import { CustomerController } from '../controllers/customer.controller';
import { authenticate, checkAccountAccess } from '../middleware/auth.middleware';
import { uploadMiddleware } from '../middleware/file-upload.middleware';

const router = Router();
const communicationController = new CommunicationController();
const templateController = new TemplateController();
const customerController = new CustomerController();

// All routes require authentication
router.use(authenticate);

// Communication messages
router.get('/messages', communicationController.getMessages.bind(communicationController));
router.get('/messages/metrics', communicationController.getCommunicationMetrics.bind(communicationController));
router.get('/messages/:id', communicationController.getMessageById.bind(communicationController));
router.post('/messages', communicationController.sendMessage.bind(communicationController));
router.post('/messages/:id/reply', communicationController.replyToMessage.bind(communicationController));
router.patch('/messages/:id/read', communicationController.markMessageAsRead.bind(communicationController));

// Gmail integration
router.post('/accounts/:accountId/gmail/setup', checkAccountAccess, communicationController.setupGmailSync.bind(communicationController));
router.post('/accounts/:accountId/gmail/sync', checkAccountAccess, communicationController.syncGmailMessages.bind(communicationController));

// eBay messages
router.post('/accounts/:accountId/ebay-messages/import', 
  checkAccountAccess, 
  uploadMiddleware.single('csvFile'),
  communicationController.importEbayMessages.bind(communicationController)
);

// Customer communications
router.get('/customers/:customerId/messages/:accountId', checkAccountAccess, communicationController.getCustomerCommunications.bind(communicationController));

// Templates
router.get('/templates', templateController.getTemplates.bind(templateController));
router.get('/templates/statistics', templateController.getTemplateStatistics.bind(templateController));
router.get('/templates/:id', templateController.getTemplateById.bind(templateController));
router.post('/templates', templateController.createTemplate.bind(templateController));
router.put('/templates/:id', templateController.updateTemplate.bind(templateController));
router.post('/templates/:id/duplicate', templateController.duplicateTemplate.bind(templateController));
router.patch('/templates/:id/toggle-status', templateController.toggleTemplateStatus.bind(templateController));

export default router;
```

## Utility Classes

### Message Classifier
```typescript
// src/utils/message-classifier.ts
export class MessageClassifier {
  static classifyMessage(subject: string, content: string) {
    const text = `${subject} ${content}`.toLowerCase();
    
    // Define keywords for each category
    const categoryKeywords = {
      complaint: ['complaint', 'problem', 'issue', 'wrong', 'damaged', 'broken', 'defective', 'disappointed', 'unhappy', 'refund', 'return'],
      return_request: ['return', 'refund', 'exchange', 'money back', 'not as described', 'different than'],
      shipping_issue: ['shipping', 'delivery', 'arrived', 'tracking', 'delayed', 'lost', 'missing', 'package'],
      payment_issue: ['payment', 'charge', 'billing', 'invoice', 'paypal', 'credit card', 'transaction'],
      inquiry: ['question', 'ask', 'how', 'what', 'when', 'where', 'why', 'info', 'details', 'availability'],
      compliment: ['great', 'excellent', 'awesome', 'perfect', 'love', 'amazing', 'wonderful', 'thank you', 'thanks'],
    };

    // Priority keywords
    const priorityKeywords = {
      urgent: ['urgent', 'asap', 'immediately', 'emergency', 'critical'],
      high: ['important', 'soon', 'quickly', 'fast', 'rush'],
    };

    // Determine category
    let category = 'general';
    let maxMatches = 0;
    
    for (const [cat, keywords] of Object.entries(categoryKeywords)) {
      const matches = keywords.filter(keyword => text.includes(keyword)).length;
      if (matches > maxMatches) {
        maxMatches = matches;
        category = cat;
      }
    }

    // Determine priority
    let priority = 'normal';
    if (priorityKeywords.urgent.some(keyword => text.includes(keyword))) {
      priority = 'urgent';
    } else if (priorityKeywords.high.some(keyword => text.includes(keyword))) {
      priority = 'high';
    }

    return { category, priority };
  }
}
```

### Email Parser
```typescript
// src/utils/email-parser.ts
export class EmailParser {
  static extractContent(payload: any): { textContent: string; htmlContent: string } {
    let textContent = '';
    let htmlContent = '';

    if (payload.body && payload.body.data) {
      // Simple body
      const content = Buffer.from(payload.body.data, 'base64').toString();
      if (payload.mimeType === 'text/html') {
        htmlContent = content;
        textContent = this.stripHtml(content);
      } else {
        textContent = content;
      }
    } else if (payload.parts) {
      // Multipart body
      for (const part of payload.parts) {
        if (part.mimeType === 'text/plain' && part.body.data) {
          textContent += Buffer.from(part.body.data, 'base64').toString();
        } else if (part.mimeType === 'text/html' && part.body.data) {
          htmlContent += Buffer.from(part.body.data, 'base64').toString();
        }
      }
      
      // If we have HTML but no text, extract text from HTML
      if (htmlContent && !textContent) {
        textContent = this.stripHtml(htmlContent);
      }
    }

    return { textContent: textContent.trim(), htmlContent: htmlContent.trim() };
  }

  private static stripHtml(html: string): string {
    return html
      .replace(/<style[^>]*>.*?<\/style>/gi, '')
      .replace(/<script[^>]*>.*?<\/script>/gi, '')
      .replace(/<[^>]+>/g, '')
      .replace(/\s+/g, ' ')
      .trim();
  }
}
```

## Success Criteria

1. ✅ Gmail integration with OAuth2 authentication
2. ✅ eBay message CSV import and processing
3. ✅ Automated message classification and prioritization
4. ✅ Template system with variable substitution
5. ✅ Customer communication history tracking
6. ✅ Message threading and reply functionality
7. ✅ Communication metrics and analytics
8. ✅ Auto-response rules (foundation)
9. ✅ Customer segmentation integration
10. ✅ Multi-account message management

## Next Steps
- Plan 8: Frontend Dashboard Implementation with React/Vue.js interface