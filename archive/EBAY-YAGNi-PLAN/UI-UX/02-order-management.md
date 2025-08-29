# Order Management Interface - List-Based UI Design

## Design System Applied
- **Grid System**: 250px sidebar + flexible main content (following dashboard-design-guide.md)
- **Design Tokens**: Colors (#5B8DEF primary, status colors), Inter font, consistent spacing
- **Data Table Pattern**: 56px row height, sortable headers, hover states
- **Interactive States**: #F9FAFB hover, #5B8DEF selections, proper focus indicators

## SOLID/YAGNI Compliance
- **Single Responsibility**: Order list, filter panel, and detail view are separate components
- **Open/Closed**: Filter system extensible without modifying order list component
- **Interface Segregation**: Separate interfaces for order display, bulk actions, and status updates
- **Dependency Inversion**: Components depend on order service abstractions, not concrete implementations
- **YAGNI**: Only essential order fields displayed, detailed view for complete data

## Main Order Management Layout (1280px+ Desktop)

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│ [Logo] eBay Manager Pro   [Search................] [🔔 3] [EN ▼] [Avatar ▼]     64px height      │
├────────────┬─────────────────────────────────────────────────────────────────────────────────────┤
│            │                                                                                      │
│  SIDEBAR   │                           ORDERS MANAGEMENT                                          │
│   250px    │                                                                                      │
│            │ ┌─ Page Header ──────────────────────────────────────────────────────────────────┐   │
│ □ Dashboard│ │ Order Management                                      Account: Store1 ▼         │   │
│ ✓ Orders   │ │ 186 total orders                                    [Sync] [Export] [Settings]  │   │
│ □ Listings │ └────────────────────────────────────────────────────────────────────────────────┘   │
│ □ Products │                                                                                      │
│ □ Messages │ ┌─ Search & Filters ─────────────────────────────────────────────────────────────┐   │
│ □ Customers│ │                                                                                │   │
│ □ Import   │ │ Search: [Order #, Buyer, Item Title...........] [🔍] [Clear] [Save]           │   │
│            │ │                                                                                │   │
│ TOOLS      │ │ Status: [All ▼] Date: [Last 30 Days ▼] Amount: [Any ▼] Priority: [All ▼]     │   │
│ □ Reports  │ │                                                                                │   │
│ □ Analytics│ │ Quick Filters:                                                                 │   │
│ □ Settings │ │ [Pending: 8] [Need Tracking: 5] [Shipped: 34] [Issues: 2] [High Value: 12]   │   │
│            │ └────────────────────────────────────────────────────────────────────────────────┘   │
│            │                                                                                      │
│            │ ┌─ Bulk Actions ─────────────────────────────────────────────────────────────────┐   │
│            │ │ Selected: 0 │ [Select All] [Select Filtered] [Clear Selection]                │   │
│            │ │ [Update Status ▼] [Add Tracking] [Export CSV] [Print Labels] [Send Messages]   │   │
│            │ └────────────────────────────────────────────────────────────────────────────────┘   │
│            │                                                                                      │
│            │ ┌─ Order Data Table ─────────────────────────────────────────────────────────────┐   │
│            │ │                                                                                │   │
│            │ │ ☐ │ Order # ↓        │ Date   │ Customer         │ Item Title     │ Amount │Status│ │
│            │ ├───────────────────────────────────────────────────────────────────────────────────┤   │
│            │ │ ☐ │ 18-13469-81867  │ Aug-21 │ mark celinko     │ Spider Farmer  │ $96.23 │⚠Track│ │
│            │ │   │                 │        │ (marcelink-0)    │ Controller     │        │      │ │
│            │ │   │                 │        │ NY, US           │ w/Bluetooth    │        │[•••] │ │
│            │ ├───────────────────────────────────────────────────────────────────────────────────┤   │
│            │ │ ☐ │ 21-13446-31215  │ Aug-17 │ Allison Price    │ Harry Potter   │ $46.20 │✓Ship │ │
│            │ │   │                 │        │ (ammart05)       │ Order Phoenix  │        │      │ │
│            │ │   │                 │        │ IL, US           │ Book-5         │        │[•••] │ │
│            │ ├───────────────────────────────────────────────────────────────────────────────────┤   │
│            │ │ ☐ │ 19-13445-28394  │ Aug-16 │ John Smith       │ Douay-Rheims   │ $42.00 │📦Proc│ │
│            │ │   │                 │        │ (bookworm123)    │ Bible Leather  │        │      │ │
│            │ │   │                 │        │ TX, US           │ Edition        │        │[•••] │ │
│            │ ├───────────────────────────────────────────────────────────────────────────────────┤   │
│            │ │ ☐ │ 17-13444-15672  │ Aug-15 │ Sarah Johnson    │ Cat Kid Comic  │ $43.00 │⏳Pend│ │
│            │ │   │                 │        │ (sarahj_reads)   │ Club 1-5 Pack  │        │      │ │
│            │ │   │                 │        │ CA, US           │ By Dav Pilkey  │        │[•••] │ │
│            │ ├───────────────────────────────────────────────────────────────────────────────────┤   │
│            │ │ ☐ │ 16-13443-09821  │ Aug-14 │ Mike Wilson      │ Heartstopper   │ $41.00 │⚠Issue│ │
│            │ │   │                 │        │ (mikew_comics)   │ 1-4 Box Set    │        │      │ │
│            │ │   │                 │        │ FL, US           │ By Alice       │        │[•••] │ │
│            │ └───────────────────────────────────────────────────────────────────────────────────┘   │
│            │                                                                                      │
│            │ ┌─ Order Details Panel (Expandable) ────────────────────────────────────────────┐   │
│            │ │ Order: 18-13469-81867 │ Status: Need Tracking │ [Close ×]                    │   │
│            │ ├──────────────────────────────────────────────────────────────────────────────────┤   │
│            │ │ Customer: mark celinko (marcelink-0) │ Item: Spider Farmer Controller        │   │
│            │ │ Email: markcelinko@yahoo.com         │ SKU: SpiderFarmer                     │   │
│            │ │ Location: Port Jervis, NY            │ Amount: $96.23                        │   │
│            │ │ Payment: PayPal ✓                    │ Ship By: Sep-01-25                    │   │
│            │ │                                                                              │   │
│            │ │ [Add Tracking] [Update Status] [Print Label] [Send Message] [View Details]   │   │
│            │ └──────────────────────────────────────────────────────────────────────────────────┘   │
│            │                                                                                      │
│            │ ┌─ Pagination ───────────────────────────────────────────────────────────────────┐   │
│            │ │ 1-20 of 186 orders │ [◀] [1] [2] [3] ... [10] [▶] │ 20 per page [▼]         │   │
│            │ └────────────────────────────────────────────────────────────────────────────────┘   │
└────────────┴─────────────────────────────────────────────────────────────────────────────────────┘
```

## Component Specifications (Following Design Guide)

### Header Component  
- **Height**: 64px
- **Background**: #FFFFFF  
- **Border-bottom**: 1px solid #E5E7EB
- **Font**: Inter, 14px

### Sidebar Navigation
- **Width**: 250px
- **Background**: #FFFFFF
- **Active item**: #5B8DEF background, white text
- **Hover**: #F3F4F6 background
- **Item height**: 44px

### Data Table (Order List)
- **Background**: #FFFFFF
- **Border-radius**: 12px
- **Shadow**: 0 1px 3px rgba(0,0,0,0.1)
- **Header**: #F8F9FC background, 14px, 600 weight
- **Row height**: 56px
- **Hover state**: #F9FAFB background
- **Selected row**: #EFF6FF background, #5B8DEF left border
- **Border between rows**: 1px solid #F3F4F6

### Form Elements
- **Search input**: 40px height, #F3F4F6 background
- **Dropdown buttons**: 32px height, #FFFFFF background
- **Primary buttons**: #5B8DEF background, white text
- **Secondary buttons**: white background, #5B8DEF border

### Status Indicators
- **Pending**: ⏳ #F59E0B (warning yellow)
- **Processing**: 📦 #3B82F6 (info blue)  
- **Shipped**: ✓ #22C55E (success green)
- **Issues**: ⚠ #EF4444 (error red)

## Mobile Layout (768px and below)

```
┌─────────────────────────────────────────┐
│ [☰] Orders      │ Store1 ▼ │ [🔔]      │
├─────────────────────────────────────────┤
│                                         │
│ ┌─ Search ────────────────────────────┐ │
│ │ [Search orders............] [🔍]   │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ ┌─ Quick Filters ─────────────────────┐ │
│ │ [All] [Pending] [Shipped] [Issues]  │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ ┌─ Order Row ─────────────────────────┐ │
│ │ ☐ 18-13469-81867    Aug-21    $96.23│ │
│ │ mark celinko (marcelink-0)          │ │
│ │ Spider Farmer Controller...         │ │
│ │ Status: ⚠ Need Tracking             │ │
│ │ [Track] [Details] [Message]         │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ ┌─ Order Row ─────────────────────────┐ │
│ │ ☐ 21-13446-31215    Aug-17    $46.20│ │
│ │ Allison Price (ammart05)            │ │
│ │ Harry Potter Order Phoenix...       │ │
│ │ Status: ✓ Shipped                   │ │
│ │ [View] [Track] [Message]            │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ ┌─ Bulk Actions ──────────────────────┐ │
│ │ Selected: 0 │ [Actions ▼]          │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ [Load More Orders]                      │
└─────────────────────────────────────────┘
```

## SOLID Component Architecture

### Order Management Components (Single Responsibility)
```typescript
// Main container - handles layout only
interface OrderManagementProps {
  currentAccount: Account;
  filters: OrderFilters;
}

<OrderManagementContainer>
  <OrderFilters onFilterChange={handleFilterChange} />
  <OrderBulkActions selectedOrders={selectedOrders} />
  <OrderList orders={filteredOrders} onSelectionChange={handleSelection} />
  <OrderDetailsPanel selectedOrder={selectedOrder} />
</OrderManagementContainer>

// Individual components with single responsibilities
<OrderFilters>         // Handles only filtering logic
<OrderList>            // Handles only order display
<OrderBulkActions>     // Handles only bulk operations  
<OrderDetailsPanel>    // Handles only order details
<OrderStatusUpdater>   // Handles only status changes
```

### Interface Segregation Examples
```typescript
// Read-only order display
interface OrderDisplayData {
  readonly orderNumber: string;
  readonly date: string;
  readonly buyer: BuyerInfo;
  readonly item: ItemSummary;
  readonly amount: number;
  readonly status: OrderStatus;
}

// Order actions interface
interface OrderActions {
  updateStatus: (orderId: string, status: OrderStatus) => Promise<void>;
  addTracking: (orderId: string, tracking: TrackingInfo) => Promise<void>;
  exportOrders: (orderIds: string[]) => Promise<void>;
  sendMessage: (orderId: string, message: string) => Promise<void>;
}

// Bulk operations interface (separate from single order actions)
interface OrderBulkActions {
  bulkStatusUpdate: (orderIds: string[], status: OrderStatus) => Promise<void>;
  bulkTrackingAdd: (orders: OrderTrackingPair[]) => Promise<void>;
  bulkExport: (orderIds: string[], format: ExportFormat) => Promise<void>;
}
```

## Mobile Layout (768px and below)

```
┌─────────────────────────────────────────┐
│ Orders          │ Store1 ▼ │ ☰ Menu    │
├─────────────────────────────────────────┤
│                                         │
│ ┌─ Search & Filters ───────────────────┐ │
│ │ [Search orders................] [🔍] │ │
│ │                                     │ │
│ │ [Pending: 8] [Need Track: 5] [All] │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ ┌─ Order Card ────────────────────────┐ │
│ │ ☐ 18-13469-81867 │ Aug-21    $96.23│ │
│ │ mark celinko                        │ │
│ │ Spider Farmer Controller...         │ │
│ │ Status: ⚠ Need Tracking            │ │
│ │ [Track] [Details] [Message]        │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ ┌─ Order Card ────────────────────────┐ │
│ │ ☐ 21-13446-31215 │ Aug-17    $46.20│ │
│ │ Allison Price                       │ │
│ │ Harry Potter Order Phoenix...       │ │
│ │ Status: ✓ Shipped                  │ │
│ │ [View] [Track] [Message]           │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ ┌─ Bulk Actions ──────────────────────┐ │
│ │ Selected: 0 │ [Select All]         │ │
│ │ [Update Status] [Export]           │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ [Load More Orders]                      │
└─────────────────────────────────────────┘
```

## Order Status Workflow (YAGNI Compliant)

```
┌─ Status Pipeline ──────────────────────────────────────┐
│                                                        │
│ [Pending] → [Processing] → [Shipped] → [Delivered]     │
│    ↓            ↓            ↓           ↓             │
│ [Cancelled]  [On Hold]   [In Transit] [Returned]      │
│                          [Lost/Damaged] [Refunded]    │
│                                                        │
│ Status Actions Available:                              │
│ • Pending → Processing (Add tracking optional)        │
│ • Processing → Shipped (Tracking required)            │  
│ • Shipped → Delivered (Auto or manual)                │
│ • Any → Cancelled/On Hold/Issue (Reason required)     │
│                                                        │
└────────────────────────────────────────────────────────┘
```

## CSV Data Mapping (Based on Real eBay Format)

```typescript
// Essential fields for order list display (YAGNI)
interface OrderListItem {
  orderNumber: string;        // "Order Number" 
  salesRecordNumber: string;  // "Sales Record Number"
  buyerUsername: string;      // "Buyer Username"
  buyerName: string;         // "Buyer Name"
  itemTitle: string;         // "Item Title" (truncated)
  totalPrice: number;        // "Total Price"
  saleDate: string;          // "Sale Date"
  shippingService: string;   // "Shipping Service"
  trackingNumber?: string;   // "Tracking Number"
  status: OrderStatus;       // Derived from multiple fields
}

// Complete order details (loaded on demand)
interface OrderDetails {
  // Customer Information
  buyerEmail: string;        // "Buyer Email"
  buyerNote?: string;        // "Buyer Note"
  shipToName: string;        // "Ship To Name"
  shipToPhone?: string;      // "Ship To Phone"
  shipToAddress: Address;    // Multiple "Ship To" fields
  
  // Item Information
  itemNumber: string;        // "Item Number"
  customLabel?: string;      // "Custom Label"
  quantity: number;          // "Quantity"
  soldFor: number;           // "Sold For"
  shippingHandling: number;  // "Shipping And Handling"
  
  // Payment Information
  paymentMethod: string;     // "Payment Method"
  paidOnDate?: string;       // "Paid On Date"
  paypalTransactionId?: string; // "PayPal Transaction ID"
  
  // Tax and Fees
  sellerCollectedTax: number;   // "Seller Collected Tax"
  ebayCollectedTax: number;     // "eBay Collected Tax"
  ebayCollectedCharges: number; // "eBay Collected Charges"
  
  // Fulfillment Information
  shipByDate: string;        // "Ship By Date"
  minDeliveryDate: string;   // "Minimum Estimated Delivery Date"
  maxDeliveryDate: string;   // "Maximum Estimated Delivery Date"
  shippedOnDate?: string;    // "Shipped On Date"
  
  // Feedback and Notes
  feedbackLeft?: string;     // "Feedback Left"
  feedbackReceived?: string; // "Feedback Received"
  myItemNote?: string;       // "My Item Note"
}
```

## Bulk Operations Workflow

### Bulk Status Update
```
1. User selects orders via checkboxes
2. Clicks "Update Status" dropdown
3. Selects new status from available transitions
4. For certain statuses, additional form appears:
   - Shipping: Requires tracking number and service
   - Cancelled: Requires cancellation reason
   - Issue: Requires issue description
5. Confirms bulk update
6. System processes orders individually
7. Progress bar shows completion
8. Results summary with any errors
```

### Bulk Tracking Addition  
```
1. User selects orders needing tracking
2. Clicks "Add Tracking" button
3. Options:
   - Single tracking for all orders
   - Upload CSV with order → tracking mapping
   - Individual entry form for each order
4. Validates tracking numbers
5. Updates orders and changes status to "Shipped"
6. Sends tracking notifications if enabled
```

## Filter System (Extensible Design)

```typescript
// Base filter interface (Open/Closed Principle)
interface OrderFilter {
  apply(orders: Order[]): Order[];
  getDisplayName(): string;
}

// Concrete filter implementations
class StatusFilter implements OrderFilter {
  constructor(private status: OrderStatus) {}
  apply(orders: Order[]): Order[] {
    return orders.filter(order => order.status === this.status);
  }
  getDisplayName() { return `Status: ${this.status}`; }
}

class DateRangeFilter implements OrderFilter {
  constructor(private startDate: Date, private endDate: Date) {}
  apply(orders: Order[]): Order[] {
    return orders.filter(order => 
      order.saleDate >= this.startDate && order.saleDate <= this.endDate
    );
  }
  getDisplayName() { return `Date: ${this.startDate} - ${this.endDate}`; }
}

// Filter manager (can add new filters without modifying existing code)
class FilterManager {
  private filters: OrderFilter[] = [];
  
  addFilter(filter: OrderFilter) {
    this.filters.push(filter);
  }
  
  applyFilters(orders: Order[]): Order[] {
    return this.filters.reduce((filtered, filter) => filter.apply(filtered), orders);
  }
}
```

## Performance Considerations (YAGNI)

### Essential Optimizations Only
- **Virtual Scrolling**: For lists > 100 orders
- **Debounced Search**: 300ms delay on search input
- **Lazy Details**: Order details loaded on panel open
- **Cached Filters**: Filter results cached for 1 minute
- **Bulk Operation Batching**: Process 50 orders at a time

### No Premature Optimization
- No complex state management until proven necessary
- No advanced caching strategies until performance issues arise
- No real-time updates unless business critical
- No advanced pagination until > 1000 orders per page

## Accessibility & Usability

### Keyboard Navigation
- Tab through all interactive elements
- Enter/Space to select orders
- Arrow keys for grid navigation
- Escape to close detail panels

### Screen Reader Support
- Order count announcements
- Status change confirmations
- Bulk operation progress updates
- Error message announcements

### Color & Status Indicators
- Status uses both color and symbols (⚠ ✓ 📦 ⏳)
- High contrast mode support
- Status changes have confirmation messages