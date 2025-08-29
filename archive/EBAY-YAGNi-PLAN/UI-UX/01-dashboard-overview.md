# Dashboard Overview - List-Based UI Design

## Design System Applied
- **Grid System**: 250px sidebar + flexible main content
- **Design Tokens**: Colors, typography, spacing from dashboard-design-guide.md
- **Component Pattern**: Data tables and lists prioritized over cards
- **Row Height**: 56px for consistency
- **Font**: Inter, -apple-system, BlinkMacSystemFont

## SOLID/YAGNI Compliance
- **Single Responsibility**: Each list section handles one metric type
- **Open/Closed**: List columns configurable without modifying core
- **Interface Segregation**: Separate interfaces for metrics, lists, and actions
- **Dependency Inversion**: Lists depend on data service abstractions
- **YAGNI**: Only essential columns visible, expandable for details

## Main Dashboard Layout (1280px+ Desktop)

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│ [Logo] eBay Manager Pro   [Search................] [🔔 3] [EN ▼] [Avatar ▼]     64px height      │
├────────────┬─────────────────────────────────────────────────────────────────────────────────────┤
│            │                                                                                      │
│  SIDEBAR   │                           MAIN CONTENT AREA                                          │
│   250px    │                                                                                      │
│            │ ┌─ Page Header ──────────────────────────────────────────────────────────────────┐   │
│ ✓Dashboard │ │ Dashboard Overview                                    Account: Store1 ▼         │   │
│ □ Orders   │ │ Last updated: 2 mins ago                            [Sync] [Export] [Settings]  │   │
│ □ Listings │ └────────────────────────────────────────────────────────────────────────────────┘   │
│ □ Products │                                                                                      │
│ □ Messages │ ┌─ KPI Summary List ─────────────────────────────────────────────────────────────┐   │
│ □ Customers│ │                                                                                │   │
│ □ Import   │ │ Metric              │ Today      │ Week       │ Month      │ YTD          │   │   │
│            │ ├────────────────────────────────────────────────────────────────────────────────┤   │
│ TOOLS      │ │ 💰 Revenue          │ $1,245     │ $8,320     │ $28,950    │ $245,600     │   │   │
│ □ Reports  │ │                     │ ↑12% ●     │ ↑8% ●      │ ↑15% ●     │ ↑22% ●       │   │   │
│ □ Analytics│ ├────────────────────────────────────────────────────────────────────────────────┤   │
│ □ Settings │ │ 📦 Orders           │ 23         │ 156        │ 642        │ 7,834        │   │   │
│            │ │                     │ ↑5% ●      │ ↓2% ●      │ ↑8% ●      │ ↑18% ●       │   │   │
│ ACCOUNT    │ ├────────────────────────────────────────────────────────────────────────────────┤   │
│ □ Profile  │ │ 📝 Active Listings  │ 456        │ +34 new    │ +127 new   │ 2,456 total  │   │   │
│ □ Billing  │ │                     │ →0% ●      │ ↑12% ●     │ ↑9% ●      │ ↑31% ●       │   │   │
│ □ Users    │ ├────────────────────────────────────────────────────────────────────────────────┤   │
│ □ Help     │ │ 💬 Messages         │ 12         │ 89         │ 356        │ 4,234        │   │   │
│ □ Logout   │ │                     │ ↑20% ●     │ ↑15% ●     │ ↑11% ●     │ ↑25% ●       │   │   │
│            │ ├────────────────────────────────────────────────────────────────────────────────┤   │
│            │ │ 👥 New Customers    │ 8          │ 45         │ 189        │ 1,245        │   │   │
│            │ │                     │ ↑33% ●     │ ↑25% ●     │ ↑18% ●     │ ↑42% ●       │   │   │
│            │ └────────────────────────────────────────────────────────────────────────────────┘   │
│            │                                                                                      │
│            │ ┌─ Order Status Pipeline List ──────────────────────────────────────────────────┐   │
│            │ │                                                                                │   │
│            │ │ Status        │ Count │ Value      │ Avg Time   │ Action Required        │   │   │
│            │ ├────────────────────────────────────────────────────────────────────────────────┤   │
│            │ │ ⏳ Pending    │ 8     │ $687.20    │ 2.3 hrs    │ [Process Now]          │   │   │
│            │ │ 📦 Processing │ 15    │ $1,245.50  │ 4.1 hrs    │ [View List]            │   │   │
│            │ │ 🚚 Shipped    │ 34    │ $2,890.40  │ 1.2 days   │ [Track All]            │   │   │
│            │ │ ✅ Delivered  │ 127   │ $10,234.80 │ 3.5 days   │ [Request Feedback]     │   │   │
│            │ │ ⚠️ Issues     │ 2     │ $156.00    │ 5.2 days   │ [Resolve Issues]       │   │   │
│            │ └────────────────────────────────────────────────────────────────────────────────┘   │
│            │                                                                                      │
│            │ ┌─ Recent Activity List ────────────────────────────────────────────────────────┐   │
│            │ │ Time    │ Type     │ Description                        │ User    │ Action  │   │   │
│            │ ├────────────────────────────────────────────────────────────────────────────────┤   │
│            │ │ 2m ago  │ Order    │ New order #18-13469-81867 received│ System  │ [View]  │   │   │
│            │ │ 5m ago  │ Message  │ Customer inquiry about shipping    │ John S. │ [Reply] │   │   │
│            │ │ 12m ago │ Listing  │ 5 items low stock alert           │ System  │ [Check] │   │   │
│            │ │ 23m ago │ Payment  │ Payment received for #21-13446    │ System  │ [View]  │   │   │
│            │ │ 45m ago │ Review   │ New 5-star review on Harry Potter │ Alice P.│ [Thank] │   │   │
│            │ │ 1h ago  │ Sync     │ CSV import completed: 156 orders  │ Admin   │ [Review]│   │   │
│            │ └────────────────────────────────────────────────────────────────────────────────┘   │
│            │                                                                                      │
│            │ ┌─ Top Products Performance List ───────────────────────────────────────────────┐   │
│            │ │ Rank │ Product                      │ Units │ Revenue  │ Margin │ Trend     │   │   │
│            │ ├────────────────────────────────────────────────────────────────────────────────┤   │
│            │ │ 1    │ Harry Potter Box Set         │ 23    │ $890.50  │ 45%    │ ↑23% ●    │   │   │
│            │ │ 2    │ Spider Farmer Controller     │ 18    │ $456.80  │ 52%    │ ↑15% ●    │   │   │
│            │ │ 3    │ Douay-Rheims Bible          │ 15    │ $234.90  │ 38%    │ ↓5% ●     │   │   │
│            │ │ 4    │ Scholastic Collection       │ 12    │ $187.20  │ 41%    │ →0% ●     │   │   │
│            │ │ 5    │ Cat Kid Comic Books         │ 9     │ $156.30  │ 48%    │ ↑8% ●     │   │   │
│            │ │                                                      [View All Products]      │   │   │
│            │ └────────────────────────────────────────────────────────────────────────────────┘   │
│            │                                                                                      │
│            │ ┌─ System Health & Alerts List ─────────────────────────────────────────────────┐   │
│            │ │ Component        │ Status    │ Usage     │ Last Check │ Details           │   │   │
│            │ ├────────────────────────────────────────────────────────────────────────────────┤   │
│            │ │ Database         │ ● Healthy │ 45% CPU   │ 30s ago    │ 234ms latency     │   │   │
│            │ │ API Gateway      │ ● Healthy │ 1.2k req/m│ 30s ago    │ All endpoints OK  │   │   │
│            │ │ CSV Processing   │ ● Active  │ 3 jobs    │ 2m ago     │ Processing orders │   │   │
│            │ │ Email Service    │ ● Healthy │ 89 sent   │ 5m ago     │ Queue: 0          │   │   │
│            │ │ Storage          │ ⚠ Warning │ 78% used  │ 10m ago    │ Clean up needed   │   │   │
│            │ └────────────────────────────────────────────────────────────────────────────────┘   │
└────────────┴─────────────────────────────────────────────────────────────────────────────────────┘
```

## Component Specifications (Following Design Guide)

### Header Component
- **Height**: 64px
- **Background**: #FFFFFF
- **Border-bottom**: 1px solid #E5E7EB
- **Padding**: 0 24px
- **Logo**: 24px height
- **Search**: 400px width, 40px height
- **Icons**: 20px size

### Sidebar Navigation  
- **Width**: 250px (collapsed: 64px)
- **Background**: #FFFFFF
- **Item height**: 44px
- **Active state**: #5B8DEF background, white text
- **Hover state**: #F3F4F6 background
- **Icon size**: 20px
- **Text**: 14px, Inter font
- **Section headers**: 12px, uppercase, #6B7280

### KPI Summary List
- **Background**: #FFFFFF
- **Border-radius**: 12px
- **Shadow**: 0 1px 3px rgba(0,0,0,0.1)
- **Header row**: #F8F9FC background, 600 font-weight
- **Row height**: 56px
- **Border between rows**: 1px solid #F3F4F6
- **Trend indicators**: Green (#22C55E) up, Red (#EF4444) down
- **Hover state**: #F9FAFB background

### Data Tables (Order Pipeline, Activities, Products)
- **Background**: #FFFFFF
- **Border-radius**: 12px
- **Header**: #F8F9FC background, 14px, 600 weight
- **Row height**: 56px
- **Hover**: #F9FAFB background
- **Actions**: Primary blue (#5B8DEF) text buttons
- **Pagination**: Bottom right, 40px height buttons

## Mobile Layout (768px and below)

```
┌─────────────────────────────────────┐
│ [☰] eBay Manager │ Store1 ▼ │ [🔔]  │
├─────────────────────────────────────┤
│                                     │
│ ┌─ Quick Stats List ─────────────┐ │
│ │ Revenue Today    $1,245 ↑12%   │ │
│ │ Orders Today     23 ↑5%        │ │
│ │ Messages         12 new         │ │
│ │ Low Stock        5 items        │ │
│ └─────────────────────────────────┘ │
│                                     │
│ ┌─ Order Pipeline ───────────────┐ │
│ │ ⏳ Pending       8 orders      │ │
│ │ 📦 Processing    15 orders     │ │
│ │ 🚚 Shipped       34 orders     │ │
│ │ ⚠️ Issues        2 orders      │ │
│ │ [View All Orders]              │ │
│ └─────────────────────────────────┘ │
│                                     │
│ ┌─ Recent Activity ──────────────┐ │
│ │ 2m  New order received         │ │
│ │ 5m  Customer message           │ │
│ │ 12m Low stock alert            │ │
│ │ [View All Activity]            │ │
│ └─────────────────────────────────┘ │
│                                     │
│ [Quick Actions ▼]                   │
└─────────────────────────────────────┘
```

## Interactive States (Design Guide Applied)

### Hover States
- **List rows**: Background #F9FAFB
- **Buttons**: Darken 10% (#4A7FE5 for primary)
- **Links**: Underline decoration
- **Transition**: 150ms ease-out

### Active/Selected States
- **Sidebar items**: #5B8DEF background, white text
- **List rows**: #EFF6FF background, #5B8DEF left border
- **Checkboxes**: #5B8DEF accent

### Loading States
```
┌────────────────────────────────────┐
│ ░░░░░░░░░░░░ │ ░░░░ │ ░░░░ │ ░░░░ │ (Skeleton loader)
│ ░░░░░░░░░░░░ │ ░░░░ │ ░░░░ │ ░░░░ │
│ ░░░░░░░░░░░░ │ ░░░░ │ ░░░░ │ ░░░░ │
└────────────────────────────────────┘
```

## Data Flow Pattern (YAGNI Compliant)

```typescript
// List-based data structure
interface DashboardListData {
  kpiMetrics: KPIRow[];        // Simple array of metrics
  orderPipeline: StatusRow[];   // Status with counts
  recentActivity: ActivityRow[]; // Time-based list
  topProducts: ProductRow[];    // Ranked list
  systemHealth: HealthRow[];    // Component status list
}

// Simple row interfaces
interface KPIRow {
  metric: string;
  today: number;
  week: number;
  month: number;
  ytd: number;
  trend: 'up' | 'down' | 'flat';
  percentage: number;
}

interface StatusRow {
  status: OrderStatus;
  count: number;
  value: number;
  avgTime: string;
  actionUrl: string;
}
```

## Performance Optimizations (Essential Only)

### List Rendering
- **Virtual scrolling**: For lists > 100 items
- **Pagination**: 20-50 items per page default
- **Lazy loading**: Load data as needed
- **Debounced search**: 300ms delay

### Data Updates
- **Polling**: Every 30 seconds for KPIs
- **WebSocket**: Real-time for critical alerts only
- **Caching**: 5-minute cache for non-critical data
- **Batch updates**: Group UI updates for efficiency

## Accessibility Features

### Keyboard Navigation
- **Tab order**: Logical flow through lists
- **Arrow keys**: Navigate within tables
- **Enter**: Activate row actions
- **Space**: Select/deselect rows

### Screen Reader Support
- **ARIA labels**: Proper table headers
- **Live regions**: For real-time updates
- **Status announcements**: Trend changes
- **Descriptive buttons**: Clear action labels

### Visual Accessibility
- **Color contrast**: 4.5:1 minimum ratio
- **Focus indicators**: 2px #5B8DEF border
- **Status icons**: Include text labels
- **Consistent spacing**: 8px grid system

## Benefits of List-Based Dashboard

1. **10x Data Density**: See 20+ metrics vs 4-6 cards
2. **Faster Scanning**: Aligned columns for easy comparison
3. **Sortable Data**: Click headers to sort any column
4. **Bulk Operations**: Select multiple rows for actions
5. **Consistent Height**: 56px rows for predictable scrolling
6. **Responsive Tables**: Horizontal scroll on mobile
7. **Export Ready**: List format easy to export as CSV