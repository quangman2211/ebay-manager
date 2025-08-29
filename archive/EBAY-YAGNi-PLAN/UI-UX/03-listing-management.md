# Listing Management Interface - List-Based UI Design

## Design System Applied
- **Grid System**: 250px sidebar + flexible main content (following dashboard-design-guide.md)
- **Design Tokens**: Colors (#5B8DEF primary, status colors), Inter font, 8px spacing grid
- **Data Table Pattern**: 56px row height, sortable columns, hover states (#F9FAFB)
- **Performance Indicators**: Color-coded stars with text labels for accessibility

## SOLID/YAGNI Compliance
- **Single Responsibility**: Active listings, draft listings, and listing editor are separate components
- **Open/Closed**: Performance metrics system extensible without modifying listing display
- **Interface Segregation**: Separate interfaces for listing display, editing, and analytics
- **Dependency Inversion**: Components depend on listing service abstractions, not CSV parsers
- **YAGNI**: Only essential listing fields in overview, detailed editor for complete data

## Main Listing Management Layout (1280px+ Desktop)

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│ [Logo] eBay Manager Pro   [Search................] [🔔 3] [EN ▼] [Avatar ▼]     64px height      │
├────────────┬─────────────────────────────────────────────────────────────────────────────────────┤
│            │                                                                                      │
│  SIDEBAR   │                         LISTING MANAGEMENT                                          │
│   250px    │                                                                                      │
│            │ ┌─ Page Header ──────────────────────────────────────────────────────────────────┐   │
│ □ Dashboard│ │ Listing Management                                    Account: Store1 ▼         │   │
│ □ Orders   │ │ Active: 456 │ Draft: 23 │ Sold: 234 │ Out of Stock: 12  [Create] [Import]     │   │
│ ✓ Listings │ └────────────────────────────────────────────────────────────────────────────────┘   │
│ □ Products │                                                                                      │
│ □ Messages │ ┌─ View Tabs & Actions ──────────────────────────────────────────────────────────┐   │
│ □ Customers│ │ [Active] [Draft] [Ended] [Performance] [Templates] │ [Create] [Import] [Export] │   │
│ □ Import   │ └────────────────────────────────────────────────────────────────────────────────┘   │
│            │                                                                                      │
│ TOOLS      │ ┌─ Search & Filters ─────────────────────────────────────────────────────────────┐   │
│ □ Reports  │ │ Search: [Title, SKU, Item Number......] [🔍] [Clear] [Save Filter]             │   │
│ □ Analytics│ │ Category: [All ▼] Format: [All ▼] Price: [Any ▼] Stock: [All ▼] Status: [All ▼]│   │
│ □ Settings │ │ Quick Filters: [Low Stock] [High Watchers] [Price Changes] [Need Photos]       │   │
│            │ └────────────────────────────────────────────────────────────────────────────────┘   │
│            │                                                                                      │
│            │ ┌─ Active Listings Data Table ──────────────────────────────────────────────────┐   │
│            │ │                                                                                │   │
│            │ │ ☐│ Item# ↓       │Img│ Title           │ SKU     │Price │Stk│Watch│Sold│Perf │Action│   │
│            │ ├────────────────────────────────────────────────────────────────────────────────────┤   │
│            │ │ ☐│ 357149671275 │📷 │ Sisters Last    │Tanbooks │$64.00│ 1 │  0  │ 2  │⭐⭐⭐ │[•••] │   │
│            │ │  │              │   │ Straw Set NEW   │         │      │   │     │    │Good │      │   │
│            │ ├────────────────────────────────────────────────────────────────────────────────────┤   │
│            │ │ ☐│ 357149759318 │📷 │ Manual Prayers  │Tanbooks │$48.00│ 2 │  0  │ 1  │⭐⭐  │[•••] │   │
│            │ │  │              │   │ Catholic NEW    │         │      │   │     │    │Avg  │      │   │
│            │ ├────────────────────────────────────────────────────────────────────────────────────┤   │
│            │ │ ☐│ 357161159921 │📷 │ Douay-Rheims    │Tanbooks │$42.00│ 1 │  2  │ 0  │⭐⭐⭐⭐│[•••] │   │
│            │ │  │              │   │ Bible Leather   │         │      │   │     │    │VGood│      │   │
│            │ ├────────────────────────────────────────────────────────────────────────────────────┤   │
│            │ │⚠ │ 357167123233 │📷 │ Bible Deluxe    │Tanbooks │$40.00│ 0 │  1  │ 0  │⭐   │[•••] │   │
│            │ │  │              │   │ Leatherette     │         │      │   │     │    │Poor │      │   │
│            │ ├────────────────────────────────────────────────────────────────────────────────────┤   │
│            │ │ ☐│ 357452926676 │📷 │ Harry Potter    │Scholar. │$68.00│ 1 │  0  │ 0  │⭐⭐⭐ │[•••] │   │
│            │ │  │              │   │ Special Edition │         │      │   │     │    │Good │      │   │
│            │ └────────────────────────────────────────────────────────────────────────────────────┘   │
│            │                                                                                      │
│            │ ┌─ Bulk Actions ─────────────────────────────────────────────────────────────────┐   │
│            │ │ Selected: 0 │ [Select All] [Select Page] [Clear Selection]                    │   │
│            │ │ [Edit Prices] [Update Stock] [End Listings] [Revise] [Promote] [Export]        │   │
│            │ └────────────────────────────────────────────────────────────────────────────────┘   │
│            │                                                                                      │
│            │ ┌─ Listing Performance Panel (Expandable) ──────────────────────────────────────┐   │
│            │ │ Item: 357161159921 - Douay-Rheims Bible Leather │ [Close ×]                   │   │
│            │ ├──────────────────────────────────────────────────────────────────────────────────┤   │
│            │ │ Views (30d): 156 │ Watchers: 2 │ Conversion: 0% │ Position: ★★★★☆               │   │
│            │ │ Suggestions: Price too high, add more photos, use promotional tools            │   │
│            │ │ [Revise] [Update Price] [Add Photos] [Promote]                                 │   │
│            │ └──────────────────────────────────────────────────────────────────────────────────┘   │
└────────────┴─────────────────────────────────────────────────────────────────────────────────────┘
```

## Component Specifications (Following Design Guide)

### Header Component  
- **Height**: 64px
- **Background**: #FFFFFF  
- **Border-bottom**: 1px solid #E5E7EB
- **Font**: Inter, 14px
- **Search bar**: 400px width, 40px height

### Sidebar Navigation
- **Width**: 250px
- **Background**: #FFFFFF
- **Active item**: #5B8DEF background, white text (Listings)
- **Hover**: #F3F4F6 background
- **Item height**: 44px

### Data Table (Active Listings)
- **Background**: #FFFFFF
- **Border-radius**: 12px
- **Shadow**: 0 1px 3px rgba(0,0,0,0.1)
- **Header**: #F8F9FC background, 14px, 600 weight
- **Row height**: 56px
- **Hover state**: #F9FAFB background
- **Selected row**: #EFF6FF background, #5B8DEF left border
- **Border between rows**: 1px solid #F3F4F6
- **Sortable headers**: Arrow indicators (↓)

### Performance Indicators  
- **Excellent**: ⭐⭐⭐⭐⭐ #22C55E (green text)
- **Very Good**: ⭐⭐⭐⭐ #3B82F6 (blue text)
- **Good**: ⭐⭐⭐ #F59E0B (yellow text)
- **Average**: ⭐⭐ #F59E0B (yellow text)
- **Poor**: ⭐ #EF4444 (red text)

### Status Indicators
- **Active**: ✓ #22C55E (success green)
- **Draft**: 📝 #F59E0B (warning yellow)
- **Ended**: ⏹ #6B7280 (neutral gray)
- **Out of Stock**: ⚠ #EF4444 (error red)

## Mobile Layout (768px and below)

```
┌─────────────────────────────────────────┐
│ [☰] Listings    │ Store1 ▼ │ [🔔]      │
├─────────────────────────────────────────┤
│                                         │
│ ┌─ Quick Stats ────────────────────────┐ │
│ │ Active: 456 │ Draft: 23             │ │
│ │ Sold: 234   │ Out of Stock: 12      │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ ┌─ View Tabs ──────────────────────────┐ │
│ │ [Active] [Draft] [Ended] [Performance] │
│ └─────────────────────────────────────┘ │
│                                         │
│ ┌─ Search ────────────────────────────┐ │
│ │ [Search listings...........] [🔍]   │ │
│ │ [All] [Low Stock] [High Watch]     │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ ┌─ Listing Row ───────────────────────┐ │
│ │ ☐ 357149671275          ⭐⭐⭐        │ │
│ │ Sisters of Last Straw Set...        │ │
│ │ SKU: Tanbooks     $64.00          │ │
│ │ Stock: 1  Watchers: 0  Sold: 2    │ │
│ │ [Edit] [Stats] [End] [Duplicate]    │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ [Load More Listings]                    │
└─────────────────────────────────────────┘
```
│ │ └─────────────────────────────┘                                 └───────────────────────────┘ │ │
│ │                                                                                                   │ │
│ │ ┌─ Optimization Suggestions ─────────────────────────────────────────────────────────────────────┐ │ │
│ │ │ 💡 Price too high - consider reducing to $38-$40 range                                        │ │ │
│ │ │ 📸 Add more photos - listings with 8+ photos get 40% more views                              │ │ │
│ │ │ 🏷️ Add promotional tool - "Fast 'N Free" badge increases watchers by 25%                     │ │ │
│ │ │ 📝 Title optimization - add "Deluxe" keyword (trending)                                       │ │ │
│ │ └───────────────────────────────────────────────────────────────────────────────────────────────┘ │ │
│ │                                                                                                   │ │
│ │ ┌─ Quick Actions ────────────────────────────────────────────────────────────────────────────────┐ │ │
│ │ │ [Revise Listing] [Update Price] [Add Promotion] [End Listing] [Duplicate] [Add to Store]      │ │ │
│ │ └───────────────────────────────────────────────────────────────────────────────────────────────┘ │ │
│ └───────────────────────────────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

## Draft Listings View

```
┌─ Draft Listings ────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                                     │
│ ┌─ Draft Progress Overview ──────────────────────────────────────────────────────────────────────────┐ │
│ │ Total Drafts: 23 │ Complete: 5 │ In Progress: 12 │ Started: 6 │ [Create New Draft]               │ │
│ └───────────────────────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                                     │
│ │SKU/Title                        │Progress│Last Edit │Status      │Actions                        │ │
│ ├───────────────────────────────────────────────────────────────────────────────────────────────────┤ │
│ │Tanbook_Prayer_Manual           │ 95%    │2 hrs ago │Ready to List│[List Now] [Preview] [Edit]    │ │
│ │Manual of Prayers Catholic NEW  │████▓   │          │            │                              │ │
│ │Missing: Photos (2)             │        │          │            │                              │ │
│ ├───────────────────────────────────────────────────────────────────────────────────────────────────┤ │
│ │Scholar_Harry_Potter_Complete   │ 78%    │1 day ago │In Progress │[Continue] [Preview] [Delete]  │ │
│ │Harry Potter Complete Series... │███▓▓   │          │            │                              │ │
│ │Missing: Description, Shipping  │        │          │            │                              │ │
│ ├───────────────────────────────────────────────────────────────────────────────────────────────────┤ │
│ │Tanbook_Bible_Leather_Deluxe   │ 45%    │3 days ago│Started     │[Continue] [Template] [Delete] │ │
│ │Bible Leather Deluxe Edition   │██▓▓▓   │          │            │                              │ │
│ │Missing: Price, Photos, Category│        │          │            │                              │ │
│ └───────────────────────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                                     │
│ ┌─ Bulk Draft Actions ───────────────────────────────────────────────────────────────────────────────┐ │
│ │ Selected: 0 │ [Select Ready] [Select All] [Apply Template] [Bulk Complete] [Export Drafts]        │ │
│ └───────────────────────────────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

## Listing Editor Interface

```
┌─ Listing Editor: Tanbook_Prayer_Manual ─────────────────────────────────────────────────────────────┐
│ [Save Draft] [Preview] [List Now] [Templates ▼] [Cancel]                          Progress: 95%     │
├─────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                     │
│ ┌─ Basic Information ─────────────────────────────────────────────────────────────────────────────────┐ │
│ │                                                                                                   │ │
│ │ Title: [A Manual of Prayers - For the Use of the Catholic Laity | 9781505128338 | NEW]           │ │
│ │        ⬜ ⬜ ⬜ ⬜ ⬜ ⬜ ⬜ ⬜ ⬜ ⬜ ⬜ ⬜ ⬜ ⬜ ⬜ ⬜ (80 characters)                     │ │
│ │                                                                                                   │ │
│ │ Category: Books > Religion & Spirituality > Christianity                        [Change]         │ │
│ │                                                                                                   │ │
│ │ SKU: [Tanbooks] Item Specifics: [Brand New ▼] [Hardcover ▼] [English ▼]                        │ │
│ │                                                                                                   │ │
│ │ eBay Product ID: [13064881334] (Auto-matched) UPC: [_____________] ISBN: [9781505128338]         │ │
│ │                                                                                                   │ │
│ └───────────────────────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                                     │
│ ┌─ Pricing & Inventory ──────────────────────────────────────────────────────────────────────────────┐ │
│ │                                                                                                   │ │
│ │ Format: ● Fixed Price  ○ Auction  ○ Buy It Now                                                   │ │
│ │                                                                                                   │ │
│ │ Price: $[48.00] Currency: [USD ▼] Quantity: [2] Available                                        │ │
│ │                                                                                                   │ │
│ │ Cost Basis: $[28.00] Estimated Profit: $15.84 (33% margin) after fees                           │ │
│ │                                                                                                   │ │
│ │ ☑ Best Offer  Min: $[44.00]  Auto Accept: $[47.00]  Auto Decline: $[42.00]                     │ │
│ │                                                                                                   │ │
│ └───────────────────────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                                     │
│ ┌─ Photos & Media ───────────────────────────────────────────────────────────────────────────────────┐ │
│ │                                                                                                   │ │
│ │ [📷 Main Photo] [📷 Photo 2] [📷 Photo 3] [➕ Add Photo] (Max: 12)                               │ │
│ │                                                                                                   │ │
│ │ ⚠ Missing: 2 additional photos recommended (current: 4, optimal: 6-8)                           │ │
│ │                                                                                                   │ │
│ │ [Upload from Device] [Copy from Similar Item] [Use Stock Photos] [Photo Templates]               │ │
│ │                                                                                                   │ │
│ └───────────────────────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                                     │
│ ┌─ Description ───────────────────────────────────────────────────────────────────────────────────────┐ │
│ │                                                                                                   │ │
│ │ [Rich Text Editor]                                                        [Templates ▼] [AI Help] │ │
│ │ ┌─────────────────────────────────────────────────────────────────────────────────────────────────┐ │ │
│ │ │ **A Manual of Prayers for Catholic Laity**                                                     │ │ │
│ │ │                                                                                                 │ │ │
│ │ │ Complete prayer manual featuring traditional Catholic prayers...                                │ │ │
│ │ │                                                                                                 │ │ │
│ │ │ **Features:**                                                                                   │ │ │
│ │ │ • 200+ pages of prayers and devotions                                                          │ │ │
│ │ │ • High-quality binding and paper                                                               │ │ │
│ │ │ • Perfect for daily devotions                                                                  │ │ │
│ │ │                                                                                                 │ │ │
│ │ │ **Shipping:**                                                                                   │ │ │
│ │ │ • Fast & Free shipping within US                                                               │ │ │
│ │ │ • Carefully packaged for protection                                                            │ │ │
│ │ └─────────────────────────────────────────────────────────────────────────────────────────────────┘ │ │
│ └───────────────────────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                                     │
│ ┌─ Shipping & Handling ──────────────────────────────────────────────────────────────────────────────┐ │
│ │                                                                                                   │ │
│ │ Domestic: ● Free Shipping  ○ Calculated  ○ Flat Rate                                            │ │
│ │ Service: [FedEx Ground ▼] Handling Time: [1 business day ▼]                                      │ │
│ │                                                                                                   │ │
│ │ International: ☑ Global Shipping Program ☑ Direct International                                  │ │
│ │ Exclude: [List of excluded countries...................] [Edit]                                 │ │
│ │                                                                                                   │ │
│ └───────────────────────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                                     │
│ [Save Draft] [Preview Listing] [Schedule] [List Now]                                               │
└─────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

## SOLID Component Architecture

### Listing Management Components (Single Responsibility)
```typescript
// Main container handles layout and state coordination
interface ListingManagementProps {
  currentAccount: Account;
  view: ListingView; // 'active' | 'draft' | 'ended' | 'performance'
}

<ListingManagementContainer>
  <ListingFilters onFilterChange={handleFilters} />
  <ListingBulkActions selectedListings={selected} />
  <ActiveListingsView listings={activeListings} />
  <DraftListingsView drafts={draftListings} />
  <ListingEditor listing={editingListing} />
  <PerformancePanel listing={selectedListing} />
</ListingManagementContainer>

// Individual components with specific responsibilities
<ListingFilters>           // Only handles filtering logic
<ActiveListingsView>       // Only displays active listings
<DraftListingsView>        // Only displays draft listings  
<ListingEditor>            // Only handles listing editing
<PerformancePanel>         // Only handles performance analytics
<BulkActionsProcessor>     // Only handles bulk operations
```

### Interface Segregation Examples
```typescript
// Read-only listing display data
interface ListingDisplayData {
  readonly itemNumber: string;
  readonly title: string;
  readonly sku: string;
  readonly price: number;
  readonly quantity: number;
  readonly watchers: number;
  readonly soldQuantity: number;
  readonly endDate: string;
  readonly performance: PerformanceRating;
}

// Listing editing interface
interface ListingEditor {
  updateTitle: (listingId: string, title: string) => Promise<void>;
  updatePrice: (listingId: string, price: number) => Promise<void>;
  updatePhotos: (listingId: string, photos: Photo[]) => Promise<void>;
  updateDescription: (listingId: string, description: string) => Promise<void>;
  saveAsDraft: (listingData: PartialListing) => Promise<void>;
  publishListing: (listingData: CompleteListing) => Promise<void>;
}

// Performance analytics interface (separate from editing)
interface ListingAnalytics {
  readonly views: number;
  readonly watchers: number;
  readonly conversion: number;
  readonly trafficSources: TrafficSource[];
  readonly suggestions: OptimizationSuggestion[];
}

// Bulk operations interface
interface ListingBulkOperations {
  bulkPriceUpdate: (listingIds: string[], priceChange: PriceChange) => Promise<void>;
  bulkStockUpdate: (updates: StockUpdate[]) => Promise<void>;
  bulkEndListings: (listingIds: string[], reason: string) => Promise<void>;
  bulkRevision: (listingIds: string[], changes: RevisionData) => Promise<void>;
}
```

## Mobile Layout (768px and below)

```
┌─────────────────────────────────────────┐
│ Listings        │ Store1 ▼ │ ☰ Menu    │
├─────────────────────────────────────────┤
│                                         │
│ ┌─ Quick Stats & Actions ──────────────┐ │
│ │ Active: 456 │ Draft: 23             │ │
│ │ [Create] [Import] [Bulk Edit]       │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ ┌─ View Tabs ──────────────────────────┐ │
│ │ [Active] [Draft] [Ended] [Stats]    │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ ┌─ Search & Filters ───────────────────┐ │
│ │ [Search listings...........] [🔍]   │ │
│ │ [All] [Low Stock] [High Watch]     │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ ┌─ Listing Card ───────────────────────┐ │
│ │ ☐ #357149671275          📊 ⭐⭐⭐   │ │
│ │ Sisters of Last Straw Set...        │ │
│ │ SKU: Tanbooks     $64.00          │ │
│ │ Stock: 1  Watchers: 0  Sold: 2    │ │
│ │ [Edit] [Stats] [End] [Duplicate]    │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ ┌─ Listing Card ───────────────────────┐ │
│ │ ☐ #357149759318          📊 ⭐⭐     │ │
│ │ Manual of Prayers Catholic...       │ │
│ │ SKU: Tanbooks     $48.00          │ │
│ │ Stock: 2  Watchers: 0  Sold: 1    │ │
│ │ [Edit] [Stats] [End] [Duplicate]    │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ [Load More Listings]                    │
└─────────────────────────────────────────┘
```

## CSV Data Mapping (Based on Real eBay Format)

```typescript
// Essential fields for listing display (YAGNI)
interface ListingDisplayData {
  itemNumber: string;          // "Item number"
  title: string;               // "Title" (truncated for display)
  customLabel: string;         // "Custom label (SKU)"
  availableQuantity: number;   // "Available quantity"
  startPrice: number;          // "Start price"
  soldQuantity: number;        // "Sold quantity"
  watchers: number;            // "Watchers"
  startDate: string;           // "Start date"
  endDate: string;             // "End date"
  ebayCategory1Name: string;   // "eBay category 1 name"
  condition: string;           // "Condition"
}

// Complete listing data for editor (loaded on demand)
interface CompleteListing {
  // Basic Information
  itemNumber: string;          // "Item number"
  title: string;               // "Title"
  variationDetails?: string;   // "Variation details"
  customLabel?: string;        // "Custom label (SKU)"
  
  // Inventory & Pricing  
  availableQuantity: number;   // "Available quantity"
  format: ListingFormat;       // "Format" (FIXED_PRICE, AUCTION, etc.)
  currency: string;            // "Currency"
  startPrice: number;          // "Start price"
  buyItNowPrice?: number;      // "Auction Buy It Now price"
  reservePrice?: number;       // "Reserve price"
  currentPrice: number;        // "Current price"
  
  // Performance Metrics
  soldQuantity: number;        // "Sold quantity"
  watchers: number;            // "Watchers"
  bids?: number;               // "Bids"
  
  // Dates & Duration
  startDate: string;           // "Start date"
  endDate: string;             // "End date"
  
  // Category & Classification
  ebayCategory1Name: string;   // "eBay category 1 name"
  ebayCategory1Number: string; // "eBay category 1 number"
  ebayCategory2Name?: string;  // "eBay category 2 name"
  ebayCategory2Number?: string;// "eBay category 2 number"
  condition: string;           // "Condition"
  
  // Product Identifiers
  ebayProductId?: string;      // "eBay Product ID(ePID)"
  upc?: string;                // "P:UPC"
  ean?: string;                // "P:EAN"
  isbn?: string;               // "P:ISBN"
  
  // Additional Fields for Editor
  listingSite: string;         // "Listing site"
  customAttributes?: CustomAttribute[]; // Various CD: and CDA: fields
}

// Draft listing progress tracking
interface DraftListing {
  id: string;
  sku: string;
  title?: string;
  completionPercentage: number;
  lastModified: string;
  status: 'started' | 'in_progress' | 'ready_to_list';
  missingFields: string[];
  validationErrors: string[];
}
```

## Performance Optimization System (YAGNI)

### Essential Performance Features
```typescript
// Performance rating calculation (simple algorithm)
interface PerformanceMetrics {
  views: number;              // 30-day views
  watchers: number;           // Current watchers
  conversion: number;         // Sold / Views ratio
  daysListed: number;         // Days since listing start
  questions: number;          // Buyer questions count
}

// Simple performance rating (no complex ML)
function calculatePerformanceRating(metrics: PerformanceMetrics): PerformanceRating {
  let score = 0;
  
  // Views score (0-25 points)
  score += Math.min(metrics.views / 10, 25);
  
  // Watchers score (0-25 points)  
  score += Math.min(metrics.watchers * 5, 25);
  
  // Conversion score (0-30 points)
  score += metrics.conversion * 30;
  
  // Time penalty (0-20 points deducted)
  score -= Math.max(0, (metrics.daysListed - 30) / 5);
  
  if (score >= 80) return 'excellent';
  if (score >= 60) return 'very_good';  
  if (score >= 40) return 'good';
  if (score >= 20) return 'average';
  return 'poor';
}

// Simple optimization suggestions (rule-based, not AI)
function generateSuggestions(listing: Listing, metrics: PerformanceMetrics): Suggestion[] {
  const suggestions: Suggestion[] = [];
  
  if (metrics.views < 20) {
    suggestions.push({
      type: 'title_optimization',
      message: 'Add trending keywords to title',
      priority: 'high'
    });
  }
  
  if (metrics.watchers === 0 && metrics.daysListed > 14) {
    suggestions.push({
      type: 'price_adjustment', 
      message: 'Consider reducing price by 5-10%',
      priority: 'high'
    });
  }
  
  return suggestions;
}
```

## Bulk Operations Workflow

### Bulk Price Update
```
1. User selects listings via checkboxes
2. Clicks "Edit Prices" from bulk actions
3. Modal appears with options:
   - Increase/Decrease by percentage
   - Increase/Decrease by fixed amount  
   - Set specific price
   - Apply pricing rules (e.g., cost + markup)
4. Preview shows old vs new prices
5. User confirms changes
6. System updates listings in batches of 25
7. Progress indicator shows completion
8. Summary report with success/failure counts
```

### Bulk Stock Update
```
1. User selects listings needing stock updates
2. Clicks "Update Stock" from bulk actions
3. Options:
   - Set specific quantity for all
   - Adjust by fixed amount (+/- N units)
   - Import from CSV (SKU → Quantity mapping)
   - Zero out stock (mark out of stock)
4. Validation prevents setting negative stock
5. Updates processed in batches
6. Listings with zero stock marked as "Out of Stock"
```

## Draft Management System

### Draft Completion Tracking
```typescript
interface DraftCompletionRules {
  required: string[];         // Fields that must be filled
  optional: string[];         // Fields that improve quality
  validationRules: ValidationRule[];
}

const LISTING_COMPLETION_RULES: DraftCompletionRules = {
  required: [
    'title',
    'category',
    'price', 
    'quantity',
    'condition',
    'main_photo',
    'description_basic'
  ],
  optional: [
    'additional_photos',
    'detailed_description', 
    'item_specifics',
    'product_identifiers',
    'shipping_preferences'
  ],
  validationRules: [
    { field: 'title', minLength: 10, maxLength: 80 },
    { field: 'price', min: 0.01, max: 999999 },
    { field: 'quantity', min: 1, max: 10000 },
    { field: 'main_photo', required: true },
    { field: 'description_basic', minLength: 50 }
  ]
};

// Calculate completion percentage
function calculateCompletion(draft: DraftListing): number {
  const requiredComplete = LISTING_COMPLETION_RULES.required
    .filter(field => draft[field] && draft[field] !== '').length;
  const requiredTotal = LISTING_COMPLETION_RULES.required.length;
  
  const optionalComplete = LISTING_COMPLETION_RULES.optional
    .filter(field => draft[field] && draft[field] !== '').length;
  const optionalTotal = LISTING_COMPLETION_RULES.optional.length;
  
  // Required fields worth 80%, optional worth 20%
  return Math.round(
    (requiredComplete / requiredTotal) * 80 + 
    (optionalComplete / optionalTotal) * 20
  );
}
```

## Template System (Extensible Design)

```typescript
// Template interface for Open/Closed Principle
interface ListingTemplate {
  id: string;
  name: string;
  category: string;
  fields: TemplateField[];
  apply(listing: DraftListing): DraftListing;
}

// Concrete template implementations
class BookListingTemplate implements ListingTemplate {
  id = 'book_template';
  name = 'Books & Publications';
  category = 'Books';
  
  fields: TemplateField[] = [
    { name: 'title', template: '{title} | {isbn} | {condition}' },
    { name: 'description', template: this.getBookDescription() },
    { name: 'item_specifics', values: ['Language: English', 'Format: {format}'] }
  ];
  
  apply(listing: DraftListing): DraftListing {
    // Apply book-specific formatting and validation
    return {
      ...listing,
      title: this.formatBookTitle(listing),
      description: this.formatBookDescription(listing),
      shipping: this.getDefaultShipping()
    };
  }
}

// Template manager (extensible without modifying existing code)
class TemplateManager {
  private templates: Map<string, ListingTemplate> = new Map();
  
  registerTemplate(template: ListingTemplate) {
    this.templates.set(template.id, template);
  }
  
  applyTemplate(templateId: string, listing: DraftListing): DraftListing {
    const template = this.templates.get(templateId);
    return template ? template.apply(listing) : listing;
  }
  
  getTemplatesForCategory(category: string): ListingTemplate[] {
    return Array.from(this.templates.values())
      .filter(t => t.category === category);
  }
}
```

## Accessibility & Usability

### Keyboard Navigation
- Tab through all listings and actions
- Arrow keys for grid navigation
- Enter/Space to open listing editor
- Escape to close modals and panels

### Screen Reader Support
- Performance ratings announced as text
- Stock levels and status changes announced
- Bulk operation progress announced
- Form validation errors read aloud

### Visual Indicators
- Performance uses stars + text (★★★ Good)
- Stock status uses icons + text (⚠ Out of Stock)
- Draft completion uses progress bars + percentages
- Actions use consistent iconography