# Product & Supplier Hub - List-Based UI Design

## Design System Applied
- **Grid System**: 250px sidebar + flexible main content (following dashboard-design-guide.md)
- **Design Tokens**: Colors (#5B8DEF primary, status colors), Inter font, consistent spacing
- **Data Table Pattern**: 56px row height, sortable headers, hover states
- **Interactive States**: #F9FAFB hover, #5B8DEF selections, proper focus indicators

## SOLID/YAGNI Compliance
- **Single Responsibility**: Product catalog, supplier management, and inventory tracking are separate components
- **Open/Closed**: Profit calculation system extensible without modifying display components
- **Interface Segregation**: Separate interfaces for product display, supplier management, and inventory operations
- **Dependency Inversion**: Components depend on product/supplier service abstractions, not CSV parsers
- **YAGNI**: Only essential inventory fields displayed, detailed analytics for specific products only

## Main Product & Supplier Hub Layout (1280px+ Desktop)

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│ [Logo] eBay Manager Pro   [Search................] [🔔 3] [EN ▼] [Avatar ▼]     64px height      │
├────────────┬─────────────────────────────────────────────────────────────────────────────────────┤
│            │                                                                                      │
│  SIDEBAR   │                       PRODUCTS & SUPPLIERS                                           │
│   250px    │                                                                                      │
│            │ ┌─ Page Header ──────────────────────────────────────────────────────────────────┐   │
│ □ Dashboard│ │ Product & Supplier Management                         Account: Store1 ▼         │   │
│ □ Orders   │ │ 234 products, 12 suppliers, 15 low stock          [Sync] [Export] [Settings]  │   │
│ □ Listings │ └────────────────────────────────────────────────────────────────────────────────┘   │
│ ✓Products  │                                                                                      │
│ □ Messages │ ┌─ Summary List ─────────────────────────────────────────────────────────────────┐   │
│ □ Customers│ │                                                                                │   │
│ □ Import   │ │ Metric          │ Count  │ Value      │ Avg Margin │ Action Required         │   │
│            │ ├────────────────────────────────────────────────────────────────────────────────┤   │
│ TOOLS      │ │ 📦 Total Stock  │ 1,234  │ $45,670    │ 48%        │ [View Inventory]        │   │
│ □ Reports  │ │ ⚠ Low Stock     │ 15     │ $2,340     │ 52%        │ [Reorder Now]           │   │
│ □ Analytics│ │ 🔄 Need Reorder │ 8      │ $1,890     │ 45%        │ [Create PO]             │   │
│ □ Settings │ │ 💰 High Profit  │ 89     │ $28,450    │ 65%        │ [View Products]         │   │
│            │ │ 📈 Top Sellers  │ 23     │ $15,670    │ 42%        │ [Analyze Trends]        │   │
│ ACCOUNT    │ └────────────────────────────────────────────────────────────────────────────────┘   │
│ □ Profile  │                                                                                      │
│ □ Billing  │ ┌─ Search & Filters ─────────────────────────────────────────────────────────────┐   │
│ □ Users    │ │                                                                                │   │
│ □ Help     │ │ Search: [SKU, Product Name, Supplier...............] [🔍] [Clear] [Save]      │   │
│ □ Logout   │ │                                                                                │   │
│            │ │ Supplier: [All ▼] Stock: [All ▼] Profit: [All ▼] Category: [All ▼]           │   │
│            │ │                                                                                │   │
│            │ │ Quick Filters:                                                                 │   │
│            │ │ [Low Stock <5] [High Profit >30%] [Top Sellers] [Need Reorder] [New Products] │   │
│            │ └────────────────────────────────────────────────────────────────────────────────┘   │
│            │                                                                                      │
│            │ ┌─ Bulk Actions ─────────────────────────────────────────────────────────────────┐   │
│            │ │ Selected: 0 │ [Select All] [Select Filtered] [Clear Selection]                │   │
│            │ │ [Update Prices] [Adjust Stock] [Reorder] [Change Supplier] [Export] [Delete]   │   │
│            │ └────────────────────────────────────────────────────────────────────────────────┘   │
│            │                                                                                      │
│            │ ┌─ Product Data Table ───────────────────────────────────────────────────────────┐   │
│            │ │                                                                                │   │
│            │ │ ☐ │ SKU ↓     │ Product           │ Supplier   │Stk│ Cost  │Sale │Mrgn│30d│St│Acts│ │
│            │ ├───────────────────────────────────────────────────────────────────────────────────┤   │
│            │ │ ☐ │ Tanbooks  │ Sisters Last      │ TAN Books  │12 │$28.00 │$64  │56% │2  │✓ │••• │ │
│            │ │   │           │ Straw Prayer Set  │ Inc ⭐⭐⭐⭐  │   │       │     │    │$128│  │    │ │
│            │ ├───────────────────────────────────────────────────────────────────────────────────┤   │
│            │ │ ☐ │ Scholar   │ Harry Potter      │ Scholastic │3  │$35.00 │$68  │49% │1  │⚠ │••• │ │
│            │ │   │           │ 1-7 Special Ed    │ ⭐⭐⭐⭐⭐    │   │       │     │    │$68 │  │    │ │
│            │ ├───────────────────────────────────────────────────────────────────────────────────┤   │
│            │ │ ☐ │ SpiderF   │ Spider Farmer     │ TechGrow   │8  │$45.00 │$89  │49% │3  │✓ │••• │ │
│            │ │   │           │ Controller GGS    │ LLC ⭐⭐⭐   │   │       │     │    │$267│  │    │ │
│            │ ├───────────────────────────────────────────────────────────────────────────────────┤   │
│            │ │ ☐ │ CatKid    │ Cat Kid Comic     │ Scholastic │0  │$22.00 │$43  │49% │2  │❌│••• │ │
│            │ │   │           │ Club 1-5 Pack     │ ⭐⭐⭐⭐⭐    │   │       │     │    │$86 │  │    │ │
│            │ └───────────────────────────────────────────────────────────────────────────────────┘   │
│            │                                                                                      │
│            │ ┌─ Product Details Panel (Expandable) ──────────────────────────────────────────────┐   │
│            │ │ Product: Tanbooks - Sisters Last Straw Set │ [Close ×]                        │   │
│            │ ├──────────────────────────────────────────────────────────────────────────────────┤   │
│            │ │ SKU: Tanbooks │ Stock: 12 units │ Cost: $28.00 │ Price: $64.00 │ Margin: 56%  │   │
│            │ │ Supplier: TAN Books Inc ⭐⭐⭐⭐ │ Lead: 4 days │ Min Order: 10 │ Sales: $128/30d │   │
│            │ │ Category: Books > Religion │ Added: Jun-15 │ Reorder: 5 threshold            │   │
│            │ │                                                                              │   │
│            │ │ [Edit Product] [Update Stock] [Change Price] [Reorder] [View History]       │   │
│            │ └──────────────────────────────────────────────────────────────────────────────────┘   │
│            │                                                                                      │
│            │ ┌─ Pagination ───────────────────────────────────────────────────────────────────┐   │
│            │ │ 1-20 of 234 products │ [◀] [1] [2] [3] ... [12] [▶] │ 20 per page [▼]        │   │
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

### Data Table (Product List)
- **Background**: #FFFFFF
- **Border-radius**: 12px
- **Shadow**: 0 1px 3px rgba(0,0,0,0.1)
- **Header**: #F8F9FC background, 14px, 600 weight
- **Row height**: 56px
- **Hover state**: #F9FAFB background
- **Selected row**: #EFF6FF background, #5B8DEF left border
- **Border between rows**: 1px solid #F3F4F6

### Status Indicators
- **Active**: ✓ #22C55E (success green)
- **Low Stock**: ⚠ #F59E0B (warning yellow)
- **Out of Stock**: ❌ #EF4444 (error red)
- **High Profit**: 💰 #22C55E (success green)

## Mobile Layout (768px and below)

```
┌─────────────────────────────────────────┐
│ Products        │ Store1 ▼ │ ☰ Menu    │
├─────────────────────────────────────────┤
│                                         │
│ ┌─ Quick Stats ────────────────────────┐ │
│ │ Total: 234 │ Low Stock: 15          │ │
│ │ Reorder: 8 │ Avg Margin: 48%        │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ ┌─ View Tabs ──────────────────────────┐ │
│ │ [Products] [Suppliers] [Reorder]    │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ ┌─ Search & Filters ───────────────────┐ │
│ │ [Search products...........] [🔍]   │ │
│ │ [All] [Low Stock] [High Profit]     │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ ┌─ Product Card ───────────────────────┐ │
│ │ ☐ Tanbooks - Sisters Last Straw     │ │
│ │ Stock: 12  Cost: $28  Sale: $64     │ │
│ │ Margin: 56%  Sales: 2 (30d)         │ │
│ │ Supplier: TAN Books ⭐⭐⭐⭐          │ │
│ │ [Edit] [Reorder] [View] [Stats]     │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ ┌─ Product Card ───────────────────────┐ │
│ │ ☐ Scholar - Harry Potter Special    │ │
│ │ Stock: 3 ⚠  Cost: $35  Sale: $68    │ │
│ │ Margin: 49%  Sales: 1 (30d)         │ │
│ │ Supplier: Scholastic ⭐⭐⭐⭐⭐        │ │
│ │ [Edit] [Reorder] [View] [Stats]     │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ [Load More Products]                    │
└─────────────────────────────────────────┘
```

## Performance Considerations (Essential Only)

### List Rendering
- **Virtual scrolling**: For product lists > 100 items
- **Pagination**: 20-50 products per page default
- **Lazy loading**: Product details loaded on demand
- **Debounced search**: 300ms delay for product search

### Data Updates
- **Polling**: Every 60 seconds for stock levels
- **WebSocket**: Real-time for critical stock alerts only
- **Caching**: 5-minute cache for supplier ratings
- **Batch updates**: Group inventory updates for efficiency

## Accessibility Features

### Keyboard Navigation
- **Tab order**: Logical flow through product lists
- **Arrow keys**: Navigate within product tables
- **Enter**: Open product details
- **Space**: Select/deselect products

### Screen Reader Support
- **Stock levels**: Announced as "12 units in stock"
- **Profit margins**: Announced as percentages
- **Supplier ratings**: Announced with star count
- **Reorder status**: Announced with urgency level

### Visual Accessibility
- **Color contrast**: 4.5:1 minimum ratio
- **Focus indicators**: 2px #5B8DEF border
- **Status icons**: Include text labels (✓ Active, ⚠ Low Stock)
- **Consistent spacing**: 8px grid system

## Benefits of List-Based Product Management

1. **Higher Data Density**: View 20+ products vs 4-6 cards
2. **Easy Comparison**: Aligned columns for cost/price/margin comparison
3. **Sortable Columns**: Click headers to sort by any metric
4. **Bulk Operations**: Select multiple products for updates
5. **Consistent Layout**: 56px rows for predictable scrolling
6. **Mobile Responsive**: Horizontal scroll preserves data
7. **Export Ready**: List format perfect for CSV export
