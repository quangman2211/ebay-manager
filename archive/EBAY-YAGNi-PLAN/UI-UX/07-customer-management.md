# Customer Management Dashboard - List-Based UI Design

## Design System Applied
- **Grid System**: 250px sidebar + flexible main content (following dashboard-design-guide.md)
- **Design Tokens**: Colors (#5B8DEF primary, status colors), Inter font, consistent spacing
- **Data Table Pattern**: 56px row height, sortable headers, hover states
- **Interactive States**: #F9FAFB hover, #5B8DEF selections, proper focus indicators

## SOLID/YAGNI Compliance
- **Single Responsibility**: Customer profiles, analytics, communication history, and segmentation are separate components
- **Open/Closed**: Customer segmentation system extensible without modifying customer display components
- **Interface Segregation**: Separate interfaces for customer display, analytics, communication, and lifecycle management
- **Dependency Inversion**: Components depend on customer service abstractions, not direct order/message data access
- **YAGNI**: Only essential customer insights, no complex behavioral prediction until proven necessary

## Main Customer Management Layout (1280px+ Desktop)

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│ [Logo] eBay Manager Pro   [Search................] [🔔 3] [EN ▼] [Avatar ▼]     64px height      │
├────────────┬─────────────────────────────────────────────────────────────────────────────────────┤
│            │                                                                                      │
│  SIDEBAR   │                         CUSTOMER MANAGEMENT                                         │
│   250px    │                                                                                      │
│            │ ┌─ Page Header ──────────────────────────────────────────────────────────────────┐   │
│ □ Dashboard│ │ Customer Management                               Account: Store1 ▼             │   │
│ □ Orders   │ │ 1,234 customers • 856 active • 67 new (30d)     [Add] [Import] [Export] [Help] │   │
│ □ Listings │ └────────────────────────────────────────────────────────────────────────────────┘   │
│ □ Products │                                                                                      │
│ □ Messages │ ┌─ Customer Overview List ───────────────────────────────────────────────────────┐   │
│ ✓Customers │ │                                                                                │   │
│ □ Import   │ │ Metric           │ Count │ Percentage │ Change     │ Action Required       │   │   │
│            │ ├────────────────────────────────────────────────────────────────────────────────┤   │
│ TOOLS      │ │ ⭐ VIP           │ 23    │ 2%         │ +2 (30d)   │ [Manage VIP Program]  │   │   │
│ □ Reports  │ │ 🆕 New          │ 67    │ 5%         │ +12% ↑     │ [Review Onboarding]   │   │   │
│ □ Analytics│ │ 🔄 Repeat       │ 234   │ 19%        │ +8% ↑      │ [Loyalty Campaign]    │   │   │
│ □ Settings │ │ 💰 High Value   │ 45    │ 4%         │ +3% ↑      │ [Premium Offers]      │   │   │
│            │ │ ⚠ Issues        │ 12    │ 1%         │ +2 (7d)    │ [Resolve Issues]      │   │   │
│ ACCOUNT    │ │ 😴 Inactive     │ 89    │ 7%         │ -5% ↓      │ [Win-back Campaign]   │   │   │
│ □ Profile  │ │ 👥 Regular      │ 764   │ 62%        │ +1% ↑      │ [Regular Engagement]  │   │   │
│ □ Billing  │ └────────────────────────────────────────────────────────────────────────────────┘   │
│ □ Users    │                                                                                      │
│ □ Help     │ ┌─ Search & Filters ─────────────────────────────────────────────────────────────┐   │
│ □ Logout   │ │                                                                                │   │
│            │ │ Search: [Name, username, email, order#............] [🔍] [Clear] [Save]        │   │
│            │ │                                                                                │   │
│            │ │ Segment: [All ▼] Status: [All ▼] LTV: [All ▼] Orders: [All ▼] Activity: [All ▼]│   │
│            │ │                                                                                │   │
│            │ │ Quick Segments:                                                                │   │
│            │ │ [⭐ VIP: 23] [🆕 New: 67] [🔄 Repeat: 234] [💰 High Value: 45] [⚠ Issues: 12] │   │
│            │ │ [😴 Inactive: 89] [👥 Regular: 764] [All: 1,234]                              │   │
│            │ └────────────────────────────────────────────────────────────────────────────────┘   │
│            │                                                                                      │
│            │ ┌─ Bulk Actions ─────────────────────────────────────────────────────────────────┐   │
│            │ │ Selected: 0 │ [Select All] [Select Filtered] [Clear Selection]                │   │
│            │ │ [Send Campaign] [Update Segment] [Export] [Tag] [Merge] [Archive]             │   │
│            │ └────────────────────────────────────────────────────────────────────────────────┘   │
│            │                                                                                      │
│            │ ┌─ Customer Data Table ──────────────────────────────────────────────────────────┐   │
│            │ │                                                                                │   │
│            │ │ ☐ │ Customer ↓           │ Seg │ Orders │ LTV     │ Last    │Status│Comm│Acts │   │
│            │ ├────────────────────────────────────────────────────────────────────────────────┤   │
│            │ │ ☐ │ ⭐ mark celinko      │ VIP │ 8      │ $734.50 │ Aug-21  │ ✅   │📧 2│••• │   │
│            │ │   │ marcelink-0          │     │        │         │         │      │⏰ 2h│    │   │
│            │ │   │ markcelinko@yahoo... │     │        │         │         │      │     │    │   │
│            │ ├────────────────────────────────────────────────────────────────────────────────┤   │
│            │ │ ☐ │ 🆕 Allison Price     │ New │ 1      │ $46.20  │ Aug-17  │ ✅   │✅ 1 │••• │   │
│            │ │   │ ammart05             │     │        │         │         │      │📧 D │    │   │
│            │ │   │ 0081ce6ad64040e5@... │     │        │         │         │      │     │    │   │
│            │ ├────────────────────────────────────────────────────────────────────────────────┤   │
│            │ │ ☐ │ 🔄 John Smith        │ Rpt │ 4      │ $168.00 │ Aug-16  │ ✅   │📧 3 │••• │   │
│            │ │   │ bookworm123          │     │        │         │         │      │⭐ 5 │    │   │
│            │ │   │ john.smith.books@... │     │        │         │         │      │     │    │   │
│            │ ├────────────────────────────────────────────────────────────────────────────────┤   │
│            │ │ ☐ │ ⚠ Mike Wilson        │ Iss │ 2      │ $84.00  │ Aug-14  │ ❌   │📧 1 │••• │   │
│            │ │   │ mikew_comics         │     │        │         │         │      │❌ R │    │   │
│            │ │   │ mike.w.comics@...    │     │        │         │         │      │     │    │   │
│            │ ├────────────────────────────────────────────────────────────────────────────────┤   │
│            │ │ ☐ │ 😴 Emma Rodriguez    │ Ina │ 3      │ $127.50 │ May-15  │ ⚠    │💌 W │••• │   │
│            │ │   │ emmar_reads          │     │        │         │         │      │📧 0 │    │   │
│            │ │   │ emma.rod.books@...   │     │        │         │         │      │     │    │   │
│            │ └────────────────────────────────────────────────────────────────────────────────┘   │
│            │                                                                                      │
│            │ ┌─ Customer Detail Panel (Expandable) ──────────────────────────────────────────┐   │
│            │ │ Customer: mark celinko (marcelink-0) │ Segment: ⭐ VIP │ [Close ×]            │   │
│ ├───────────────────────────────────────────────────────────────────────────────────────────────────┤ │
│ │                                                                                                   │ │
│ │ ┌─ Profile Summary ──────────────────┐ ┌─ Metrics & Analytics ───────────────┐ ┌─ Communication ─┐ │ │
│ │ │ Name: mark celinko               │ │ Customer Since: Jun 2023             │ │ Last Contact:   │ │ │
│ │ │ Username: marcelink-0            │ │ Total Orders: 8                      │ │ 2 hours ago     │ │ │
│ │ │ Email: markcelinko@yahoo.com     │ │ Lifetime Value: $734.50              │ │                 │ │ │
│ │ │ Phone: +1 845-754-5571           │ │ Average Order: $91.81                │ │ Response Time:  │ │ │
│ │ │                                  │ │ Order Frequency: 45 days             │ │ 2.1h avg        │ │ │
│ │ │ Primary Address:                 │ │ Last Order: Aug 21, 2025             │ │                 │ │ │
│ │ │ 18 Cahoonzie St                  │ │ Days Since Last: 3 days              │ │ Messages: 12    │ │ │
│ │ │ Port Jervis, NY 12771            │ │                                      │ │ ✅ 10 resolved  │ │ │
│ │ │ United States                    │ │ Satisfaction: ⭐⭐⭐⭐⭐ (5.0)        │ │ ⏰ 2 pending    │ │ │
│ │ │                                  │ │ Returns: 0 (0%)                      │ │                 │ │ │
│ │ │ Added: Jun 15, 2023              │ │ Disputes: 0                          │ │ [View All]      │ │ │
│ │ │ Updated: Aug 21, 2025            │ │ Risk Score: Low                      │ │ [Send Message]  │ │ │
│ │ └──────────────────────────────────┘ └──────────────────────────────────────┘ └─────────────────┘ │ │
│ │                                                                                                   │ │
│ │ ┌─ Order History ────────────────────────────────────────────────────────────────────────────────┐ │ │
│ │ │ Date       │Order Number   │Items                     │Amount │Status    │Notes              │ │ │
│ │ │ ├──────────────────────────────────────────────────────────────────────────────────────────────┤ │ │
│ │ │ Aug-21     │18-13469-81867 │Spider Farmer Controller  │$96.23 │🔄 Shipped│Needs tracking     │ │ │
│ │ │ Jul-05     │17-13298-45632 │Prayer Manual Set         │$64.00 │✅ Complete│⭐ 5-star review   │ │ │
│ │ │ May-22     │16-13187-23456 │Bible Study Collection    │$89.50 │✅ Complete│Fast delivery      │ │ │
│ │ │ Apr-03     │15-13098-78901 │Christian Books Bundle    │$145.75│✅ Complete│Repeat customer    │ │ │
│ │ │ ... 4 more orders                                                      │[View All]         │ │ │
│ │ └────────────────────────────────────────────────────────────────────────────────────────────────┘ │ │
│ │                                                                                                   │ │
│ │ ┌─ Purchase Behavior Analysis ───────────────────────────────────────────────────────────────────┐ │ │
│ │ │ Preferred Categories: Books (75%), Religious (60%), Educational (15%)                         │ │ │
│ │ │ Favorite Brands: TAN Books, Scholastic, Christian Publications                                │ │ │
│ │ │ Price Range: $40-$150 (sweet spot: $65-$95)                                                   │ │ │
│ │ │ Shopping Pattern: Regular buyer, orders every 6-8 weeks                                       │ │ │
│ │ │ Seasonal Trends: Higher activity in Sep-Nov (back to school season)                          │ │ │
│ │ │                                                                                                │ │ │
│ │ │ 💡 Recommendations:                                                                           │ │ │
│ │ │ • Send new TAN Books releases                                                                 │ │ │
│ │ │ • Offer bulk discounts for $100+ orders                                                      │ │ │
│ │ │ • Target back-to-school campaigns in late August                                              │ │ │
│ │ └────────────────────────────────────────────────────────────────────────────────────────────────┘ │ │
│ │                                                                                                   │ │
│ │ ┌─ Tags & Notes ─────────────────────────────────────────────────────────────────────────────────┐ │ │
│ │ │ Tags: [VIP Customer] [Repeat Buyer] [Religious Books] [Fast Payer] [+Add Tag]                 │ │ │
│ │ │                                                                                                │ │ │
│ │ │ Private Notes:                                                                                 │ │ │
│ │ │ • Greenhouse owner, interested in garden/farming books                                        │ │ │
│ │ │ • Prefers FedEx shipping, always tips/thanks in messages                                      │ │ │
│ │ │ • Good candidate for exclusive offers and early access                                        │ │ │
│ │ │ [Edit Notes]                                                                                  │ │ │
│ │ └────────────────────────────────────────────────────────────────────────────────────────────────┘ │ │
│ │                                                                                                   │ │
│ │ ┌─ Quick Actions ────────────────────────────────────────────────────────────────────────────────┐ │ │
│ │ │ [Send Personal Message] [Add to VIP List] [Create Support Ticket] [Update Profile] [Export]   │ │ │
│ │ │ [View All Orders] [Block Customer] [Merge with Another] [Send Product Recommendations]        │ │ │
│ │ └────────────────────────────────────────────────────────────────────────────────────────────────┘ │ │
│ └───────────────────────────────────────────────────────────────────────────────────────────────────┘ │
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

### Customer Data Table
- **Background**: #FFFFFF
- **Border-radius**: 12px
- **Shadow**: 0 1px 3px rgba(0,0,0,0.1)
- **Header**: #F8F9FC background, 14px, 600 weight
- **Row height**: 56px
- **Hover state**: #F9FAFB background
- **Selected row**: #EFF6FF background, #5B8DEF left border
- **Border between rows**: 1px solid #F3F4F6

### Status Indicators
- **VIP**: ⭐ #F59E0B (gold)
- **New**: 🆕 #22C55E (success green)
- **Repeat**: 🔄 #3B82F6 (info blue)
- **Issues**: ⚠ #EF4444 (error red)
- **Inactive**: 😴 #6B7280 (gray)
- **Active**: ✅ #22C55E (success green)

## Mobile Layout (768px and below)

```
┌─────────────────────────────────────────┐
│ Customers       │ Store1 ▼ │ ☰ Menu    │
├─────────────────────────────────────────┤
│                                         │
│ ┌─ Overview ───────────────────────────┐ │
│ │ Total: 1,234 │ VIP: 23 │ New: 67   │ │
│ │ LTV: $156.80 │ Repeat: 67%         │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ ┌─ Segments ───────────────────────────┐ │
│ │ [All] [VIP] [New] [Repeat] [Issues] │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ ┌─ Search & Filter ────────────────────┐ │
│ │ [Search customers...........] [🔍]  │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ ┌─ Customer Card ──────────────────────┐ │
│ │ ☐ ⭐ mark celinko                   │ │
│ │ marcelink-0                         │ │
│ │ 8 orders • $734.50 LTV              │ │
│ │ Last: Aug-21 • 📧 2 pending         │ │
│ │ [View] [Message] [Orders]           │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ ┌─ Customer Card ──────────────────────┐ │
│ │ ☐ 🆕 Allison Price                  │ │
│ │ ammart05                            │ │
│ │ 1 order • $46.20 LTV                │ │
│ │ Last: Aug-17 • ✅ Delivered         │ │
│ │ [View] [Message] [Orders]           │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ [Load More Customers]                   │
└─────────────────────────────────────────┘
```

## Customer Analytics Dashboard

```
┌─ Customer Analytics & Insights ─────────────────────────────────────────────────────────────────────┐
│                                                                                                     │
│ ┌─ Key Performance Indicators ────────────────────────────────────────────────────────────────────────┐ │
│ │                                                                                                   │ │
│ │ ┌─ Customer Growth ────────────┐ ┌─ Lifetime Value ─────────────┐ ┌─ Retention ─────────────────┐ │ │
│ │ │ New Customers (30d):     67  │ │ Average LTV:       $156.80   │ │ Repeat Rate:        67%     │ │ │
│ │ │ Growth Rate:           +12%  │ │ VIP Customers:     23 (2%)   │ │ Churn Rate:         15%     │ │ │
│ │ │ Acquisition Cost:      $8.50 │ │ High Value (>$500): 45 (4%)  │ │ 90-Day Return:      78%     │ │ │
│ │ │ Monthly Trend:          ↗    │ │ Total Customer LTV: $193,588 │ │ Avg Time Between:   52d     │ │ │
│ │ └──────────────────────────────┘ └──────────────────────────────┘ └─────────────────────────────┘ │ │
│ └───────────────────────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                                     │
│ ┌─ Customer Segmentation Analysis ────────────────────────────────────────────────────────────────────┐ │
│ │                                                                                                   │ │
│ │ ┌─ Segment Distribution ───────────────────────────────────────────────────────────────────────────┐ │ │
│ │ │                                                                                                 │ │ │
│ │ │ ⭐ VIP (23)        ████                    │ 💰 High LTV: $500+ avg                           │ │ │
│ │ │ 🔄 Repeat (234)   ████████████████        │ 📈 Revenue Impact: 45% of total                  │ │ │
│ │ │ 🆕 New (67)       ████                    │ 🎯 Growth Potential: High                        │ │ │
│ │ │ 💰 High Value (45)██                      │ ⚠ Risk Level: Low                                │ │ │
│ │ │ ⚠ Issues (12)     █                       │                                                   │ │ │
│ │ │ 😴 Inactive (89)  █████                   │ Segments by Behavior:                             │ │ │
│ │ │ 👥 Regular (764)  ████████████████████████│ • Deal Seekers: 34% (price sensitive)            │ │ │
│ │ │                                           │ • Quality Focused: 28% (premium buyers)           │ │ │
│ │ │ [Customize Segments] [Create New Segment] │ • Browsers: 23% (low conversion)                  │ │ │
│ │ │                                           │ • Loyalists: 15% (brand/store loyal)             │ │ │
│ │ └─────────────────────────────────────────────────────────────────────────────────────────────────┘ │ │
│ └───────────────────────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                                     │
│ ┌─ Customer Journey & Lifecycle Analysis ────────────────────────────────────────────────────────────┐ │
│ │                                                                                                   │ │
│ │ ┌─ Acquisition Funnel ───────────────────────────────────────────────────────────────────────────┐ │ │
│ │ │ Website Visitors: 12,450 →  Browsers: 3,680 →  First Purchase: 234 →  Repeat: 156            │ │ │
│ │ │      (100%)                    (30%)              (1.9%)               (1.3%)                 │ │ │
│ │ │                                                                                                 │ │ │
│ │ │ Conversion Bottlenecks:                                                                         │ │ │
│ │ │ • Browse to Cart: 67% (good)                                                                   │ │ │
│ │ │ • Cart to Purchase: 23% (needs improvement)                                                    │ │ │
│ │ │ • First to Second Purchase: 67% (good)                                                         │ │ │
│ │ └─────────────────────────────────────────────────────────────────────────────────────────────────┘ │ │
│ │                                                                                                   │ │
│ │ ┌─ Lifecycle Stages ─────────────────────────────────────────────────────────────────────────────┐ │ │
│ │ │ 🆕 New (0-30d):        67 customers │ Focus: Onboarding & first experience                   │ │ │
│ │ │ 🌱 Developing (31-90d): 89 customers │ Focus: Second purchase encouragement                   │ │ │
│ │ │ 🔄 Active (91-365d):   456 customers │ Focus: Regular engagement & retention                  │ │ │
│ │ │ ⭐ VIP (365d+):        123 customers │ Focus: Loyalty rewards & exclusive offers             │ │ │
│ │ │ 😴 At Risk (180d+):     89 customers │ Focus: Win-back campaigns                              │ │ │
│ │ │ 💔 Churned (365d+):     67 customers │ Focus: Re-activation attempts                          │ │ │
│ │ └─────────────────────────────────────────────────────────────────────────────────────────────────┘ │ │
│ └───────────────────────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                                     │
│ ┌─ Purchase Behavior Insights ───────────────────────────────────────────────────────────────────────┐ │
│ │                                                                                                   │ │
│ │ ┌─ Popular Categories by Segment ─────┐ ┌─ Seasonal Patterns ─────────────────┐ ┌─ Price Sensitivity ┐ │ │
│ │ │ VIP Customers:                      │ │ Q4 2024: +35% (holiday season)      │ │ $0-25:      23%    │ │ │
│ │ │ • Religious Books: 78%              │ │ Q1 2025: -12% (post-holiday)        │ │ $25-50:     45%    │ │ │
│ │ │ • Educational: 45%                  │ │ Q2 2025: +8% (spring growth)        │ │ $50-100:    23%    │ │ │
│ │ │ • Premium Items: 34%                │ │ Q3 2025: +22% (back-to-school)      │ │ $100+:      9%     │ │ │
│ │ │                                     │ │                                      │ │                    │ │ │
│ │ │ Regular Customers:                  │ │ Peak Days: Sundays, Tuesdays         │ │ Sweet Spot: $35-65 │ │ │
│ │ │ • General Books: 67%                │ │ Peak Hours: 7-9 PM EST               │ │ Bulk Buyers: 15%   │ │ │
│ │ │ • Value Items: 56%                  │ │ Seasonal Items: 23% of sales         │ │ Price Elastic: 78% │ │ │
│ │ │ • Educational: 23%                  │ │                                      │ │                    │ │ │
│ │ └─────────────────────────────────────┘ └──────────────────────────────────────┘ └────────────────────┘ │ │
│ └───────────────────────────────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

## Communication History & Engagement Tracking

```
┌─ Customer Communication Analysis ───────────────────────────────────────────────────────────────────┐
│                                                                                                     │
│ ┌─ Communication Overview ────────────────────────────────────────────────────────────────────────────┐ │
│ │                                                                                                   │ │
│ │ Total Conversations: 1,456 │ Avg Response Time: 2.3h │ Satisfaction: 4.8/5 │ Resolution: 94%     │ │
│ │                                                                                                   │ │
│ └───────────────────────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                                     │
│ │Customer                    │Messages│Last Contact│Response│Satisfaction│Issues│Status            │ │
│ ├───────────────────────────────────────────────────────────────────────────────────────────────────┤ │
│ │mark celinko (marcelink-0)  │   12   │2h ago      │1.8h    │⭐⭐⭐⭐⭐     │  0   │✅ Good Customer  │ │
│ │⭐ VIP Customer             │        │🔄 Active   │        │5.0/5       │      │                  │ │
│ ├───────────────────────────────────────────────────────────────────────────────────────────────────┤ │
│ │Allison Price (ammart05)    │    3   │1d ago      │2.1h    │⭐⭐⭐⭐⭐     │  0   │✅ New Customer   │ │
│ │🆕 New Customer             │        │📧 Email    │        │5.0/5       │      │                  │ │
│ ├───────────────────────────────────────────────────────────────────────────────────────────────────┤ │
│ │John Smith (bookworm123)    │    8   │3d ago      │1.5h    │⭐⭐⭐⭐⭐     │  0   │✅ Loyal Customer │ │
│ │🔄 Repeat Customer          │        │📧 Email    │        │5.0/5       │      │                  │ │
│ ├───────────────────────────────────────────────────────────────────────────────────────────────────┤ │
│ │Mike Wilson (mikew_comics)  │    5   │1d ago      │4.2h    │⭐⭐         │  1   │⚠ Needs Attention │ │
│ │⚠ Issue Customer           │        │❌ Return   │        │2.0/5       │      │                   │ │
│ ├───────────────────────────────────────────────────────────────────────────────────────────────────┤ │
│ │Emma Rodriguez (emmar_reads)│    2   │90d ago     │-       │⭐⭐⭐⭐      │  0   │😴 Inactive       │ │
│ │😴 Inactive Customer        │        │💌 Win-back │        │4.0/5       │      │                  │ │
│ └───────────────────────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                                     │
│ ┌─ Communication Timeline: mark celinko ─────────────────────────────────────────────────────────────┐ │
│ │                                                                                                   │ │
│ │ 📅 Aug 21, 2025 10:34 AM - Order Inquiry                                                         │ │
│ │ 👤 Customer: "Question about Spider Farmer shipment - when will it ship?"                        │ │
│ │ 🏪 Store (12:15 PM): "Thanks for your order! Shipping today, tracking in 2-3 hours."            │ │
│ │ 👤 Customer (12:23 PM): "Great, thanks for the quick response!"                                   │ │
│ │ Status: ✅ Resolved │ Satisfaction: ⭐⭐⭐⭐⭐ │ Response Time: 1.7h                              │ │
│ │                                                                                                   │ │
│ │ 📅 Jul 5, 2025 3:22 PM - Product Question                                                        │ │
│ │ 👤 Customer: "Does the Prayer Manual include morning and evening prayers?"                        │ │
│ │ 🏪 Store (3:45 PM): "Yes! It includes complete daily prayer cycles plus special occasion..."     │ │
│ │ 👤 Customer (4:12 PM): "Perfect! Just ordered. Love your detailed responses."                     │ │
│ │ Status: ✅ Led to Sale │ Satisfaction: ⭐⭐⭐⭐⭐ │ Response Time: 23min                          │ │
│ │                                                                                                   │ │
│ │ [View Full History] [Export Conversations] [Communication Preferences]                           │ │
│ └───────────────────────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                                     │
│ ┌─ Engagement Campaigns & Automation ────────────────────────────────────────────────────────────────┐ │
│ │                                                                                                   │ │
│ │ Active Campaigns:                                                                                 │ │
│ │ • New Customer Welcome Series: 67 enrolled, 78% open rate                                        │ │
│ │ • VIP Exclusive Offers: 23 enrolled, 89% engagement                                              │ │
│ │ • Win-Back Campaign: 89 enrolled, 23% response rate                                              │ │
│ │ • Order Follow-Up Series: 156 enrolled, 67% satisfaction feedback                                │ │
│ │                                                                                                   │ │
│ │ [Create New Campaign] [Campaign Performance] [Automation Rules]                                   │ │
│ └───────────────────────────────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

## SOLID Component Architecture

### Customer Management Components (Single Responsibility)
```typescript
// Main container coordinates customer data and interactions
interface CustomerManagementProps {
  currentAccount: Account;
  selectedSegment?: CustomerSegment;
}

<CustomerManagement>
  <CustomerFilters onFilterChange={handleFilters} />
  <CustomerSegmentation segments={segments} />
  <CustomerList customers={filteredCustomers} />
  <CustomerProfile selectedCustomer={selectedCustomer} />
  <CustomerAnalytics customers={customers} />
  <CommunicationHistory customerId={customerId} />
  <LifecycleManager customers={customers} />
</CustomerManagement>

// Individual components with specific responsibilities
<CustomerList>            // Only displays customer list with basic info
<CustomerProfile>         // Only shows detailed customer profile
<CustomerAnalytics>       // Only calculates and displays analytics
<CustomerSegmentation>    // Only handles customer categorization
<CommunicationHistory>    // Only manages communication tracking
<LifecycleManager>        // Only handles customer lifecycle stages
<EngagementTracker>       // Only tracks customer engagement metrics
```

### Interface Segregation Examples
```typescript
// Read-only customer display data
interface CustomerDisplayData {
  readonly id: string;
  readonly name: string;
  readonly username: string;
  readonly email: string;
  readonly segment: CustomerSegment;
  readonly totalOrders: number;
  readonly lifetimeValue: number;
  readonly lastOrderDate: string;
  readonly status: CustomerStatus;
  readonly communicationSummary: CommunicationSummary;
}

// Customer analytics interface (separate from basic display)
interface CustomerAnalytics {
  readonly totalCustomers: number;
  readonly newCustomers30d: number;
  readonly averageLifetimeValue: number;
  readonly repeatCustomerRate: number;
  readonly churnRate: number;
  readonly segmentDistribution: SegmentDistribution[];
  readonly topCustomersByLTV: CustomerSummary[];
  readonly communicationMetrics: CommunicationMetrics;
}

// Customer management interface (separate from analytics)
interface CustomerManager {
  updateCustomerInfo: (customerId: string, updates: CustomerUpdates) => Promise<void>;
  addCustomerTag: (customerId: string, tag: string) => Promise<void>;
  removeCustomerTag: (customerId: string, tag: string) => Promise<void>;
  updateSegment: (customerId: string, segment: CustomerSegment) => Promise<void>;
  addCustomerNote: (customerId: string, note: string) => Promise<void>;
  mergeCustomers: (sourceId: string, targetId: string) => Promise<void>;
}

// Communication interface (separate from customer management)
interface CustomerCommunication {
  readonly messageHistory: Message[];
  readonly responseTime: number;
  readonly satisfactionScore: number;
  readonly communicationPreferences: CommunicationPreferences;
  sendMessage: (customerId: string, message: string, template?: string) => Promise<void>;
  getCommunicationHistory: (customerId: string) => Promise<Message[]>;
  updateCommunicationPreferences: (customerId: string, prefs: CommunicationPreferences) => Promise<void>;
}
```

## Mobile Layout (768px and below)

```
┌─────────────────────────────────────────┐
│ Customers       │ Store1 ▼ │ ☰ Menu    │
├─────────────────────────────────────────┤
│                                         │
│ ┌─ Overview ───────────────────────────┐ │
│ │ Total: 1,234 │ VIP: 23 │ New: 67   │ │
│ │ LTV: $156.80 │ Repeat: 67%         │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ ┌─ Segments ───────────────────────────┐ │
│ │ [All] [VIP] [New] [Repeat] [Issues] │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ ┌─ Search & Filter ────────────────────┐ │
│ │ [Search customers...........] [🔍]  │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ ┌─ Customer Card ──────────────────────┐ │
│ │ ⭐ mark celinko                      │ │
│ │ marcelink-0                         │ │
│ │ 8 orders • $734.50 LTV              │ │
│ │ Last: Aug-21 • 📧 2 pending         │ │
│ │ [View] [Message] [Orders]           │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ ┌─ Customer Card ──────────────────────┐ │
│ │ 🆕 Allison Price                     │ │
│ │ ammart05                            │ │
│ │ 1 order • $46.20 LTV                │ │
│ │ Last: Aug-17 • ✅ Delivered         │ │
│ │ [View] [Message] [Orders]           │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ [Load More Customers]                   │
└─────────────────────────────────────────┘
```

## Customer Segmentation System (YAGNI)

```typescript
// Simple rule-based customer segmentation
type CustomerSegment = 
  | 'new'           // 0-30 days, <2 orders
  | 'regular'       // 31-365 days, 2-5 orders  
  | 'repeat'        // 2+ orders, active within 90 days
  | 'vip'           // High LTV or frequent buyer
  | 'high_value'    // LTV > $500
  | 'at_risk'       // No purchase in 90+ days
  | 'inactive'      // No purchase in 180+ days
  | 'issue'         // Has open disputes/returns
  | 'churned';      // No purchase in 365+ days

function calculateCustomerSegment(customer: Customer): CustomerSegment {
  const daysSinceLastOrder = daysBetween(customer.lastOrderDate, new Date());
  const daysSinceFirstOrder = daysBetween(customer.firstOrderDate, new Date());
  
  // Check for issues first
  if (customer.activeDisputes > 0 || customer.activeReturns > 0) {
    return 'issue';
  }
  
  // Check activity level
  if (daysSinceLastOrder > 365) return 'churned';
  if (daysSinceLastOrder > 180) return 'inactive';
  if (daysSinceLastOrder > 90 && customer.totalOrders >= 2) return 'at_risk';
  
  // Check value segments
  if (customer.lifetimeValue > 500) return 'high_value';
  if (customer.lifetimeValue > 300 && customer.totalOrders >= 5) return 'vip';
  
  // Check experience level
  if (daysSinceFirstOrder < 30 || customer.totalOrders < 2) return 'new';
  if (customer.totalOrders >= 2) return 'repeat';
  
  return 'regular';
}

// Simple LTV calculation
function calculateLifetimeValue(orders: Order[]): number {
  return orders.reduce((sum, order) => sum + order.totalAmount, 0);
}

// Customer health score (simple metrics)
function calculateCustomerHealthScore(customer: Customer): number {
  let score = 50; // Base score
  
  // Order frequency bonus
  const avgDaysBetweenOrders = customer.totalOrders > 1 
    ? daysBetween(customer.firstOrderDate, customer.lastOrderDate) / (customer.totalOrders - 1)
    : 0;
  
  if (avgDaysBetweenOrders < 30) score += 20;
  else if (avgDaysBetweenOrders < 60) score += 10;
  else if (avgDaysBetweenOrders < 90) score += 5;
  
  // Communication quality bonus
  if (customer.avgResponseTime < 24) score += 10;
  if (customer.satisfactionScore >= 4.5) score += 15;
  
  // Recency bonus/penalty
  const daysSinceLastOrder = daysBetween(customer.lastOrderDate, new Date());
  if (daysSinceLastOrder < 30) score += 15;
  else if (daysSinceLastOrder < 90) score += 5;
  else if (daysSinceLastOrder > 180) score -= 20;
  
  // Issue penalty
  score -= customer.totalDisputes * 10;
  score -= customer.totalReturns * 5;
  
  return Math.max(0, Math.min(100, score));
}
```

## Communication Analytics (Simple Tracking)

```typescript
// Communication metrics tracking
interface CommunicationMetrics {
  totalMessages: number;
  avgResponseTime: number; // Hours
  satisfactionScore: number; // 1-5 scale
  resolutionRate: number; // Percentage
  messagesByType: Record<MessageType, number>;
  responseTimeBySegment: Record<CustomerSegment, number>;
}

function calculateCommunicationMetrics(messages: Message[]): CommunicationMetrics {
  const resolvedMessages = messages.filter(m => m.status === 'resolved');
  const ratedMessages = messages.filter(m => m.satisfactionRating > 0);
  
  return {
    totalMessages: messages.length,
    avgResponseTime: messages.reduce((sum, m) => sum + (m.responseTime || 0), 0) / messages.length,
    satisfactionScore: ratedMessages.reduce((sum, m) => sum + m.satisfactionRating, 0) / ratedMessages.length,
    resolutionRate: (resolvedMessages.length / messages.length) * 100,
    messagesByType: groupBy(messages, 'type'),
    responseTimeBySegment: calculateResponseTimeBySegment(messages)
  };
}

// Customer engagement scoring
function calculateEngagementScore(customer: Customer): number {
  let score = 0;
  
  // Order engagement (40% of score)
  const orderFrequency = customer.totalOrders / Math.max(1, daysBetween(customer.firstOrderDate, new Date()) / 30);
  score += Math.min(40, orderFrequency * 10);
  
  // Communication engagement (30% of score)  
  if (customer.avgResponseTime > 0) {
    score += Math.min(30, 30 - (customer.avgResponseTime / 24) * 5); // Faster response = higher score
  }
  
  // Recency (30% of score)
  const daysSinceLastActivity = daysBetween(customer.lastActivityDate, new Date());
  if (daysSinceLastActivity < 7) score += 30;
  else if (daysSinceLastActivity < 30) score += 20;
  else if (daysSinceLastActivity < 90) score += 10;
  
  return Math.min(100, score);
}
```

## Customer Lifecycle Management

```typescript
// Simple lifecycle stage progression
type LifecycleStage = 
  | 'prospect'      // Browsed, no purchase
  | 'first_time'    // 1 order, <30 days  
  | 'developing'    // 1 order, 30-90 days
  | 'established'   // 2+ orders, active
  | 'loyal'         // 5+ orders or 12+ months
  | 'champion'      // High LTV + advocacy
  | 'at_risk'       // Declining activity
  | 'dormant';      // Long period inactive

function determineLifecycleStage(customer: Customer): LifecycleStage {
  const daysSinceFirst = daysBetween(customer.firstOrderDate, new Date());
  const daysSinceLast = daysBetween(customer.lastOrderDate, new Date());
  
  if (customer.totalOrders === 0) return 'prospect';
  
  if (daysSinceLast > 180) return 'dormant';
  if (daysSinceLast > 90 && customer.totalOrders >= 2) return 'at_risk';
  
  if (customer.lifetimeValue > 1000 && customer.satisfactionScore >= 4.5) return 'champion';
  if (customer.totalOrders >= 5 || daysSinceFirst > 365) return 'loyal';
  if (customer.totalOrders >= 2) return 'established';
  if (customer.totalOrders === 1 && daysSinceFirst > 90) return 'developing';
  
  return 'first_time';
}

// Lifecycle-based recommendations
function getLifecycleRecommendations(stage: LifecycleStage): string[] {
  const recommendations: Record<LifecycleStage, string[]> = {
    prospect: ['Send welcome offer', 'Provide product recommendations', 'Follow up browsing behavior'],
    first_time: ['Send thank you message', 'Request feedback', 'Offer complementary products'],
    developing: ['Encourage second purchase', 'Send educational content', 'Offer loyalty program'],
    established: ['Regular engagement', 'Cross-sell opportunities', 'Seasonal promotions'],
    loyal: ['VIP treatment', 'Exclusive offers', 'Early access to new products'],
    champion: ['Referral program', 'User-generated content', 'Advisory panel invitation'],
    at_risk: ['Win-back campaign', 'Special offers', 'Survey for feedback'],
    dormant: ['Re-engagement series', 'Major discount offer', 'New product announcements']
  };
  
  return recommendations[stage] || [];
}
```

## Data Privacy & GDPR Compliance (Essential Only)

```typescript
// Essential privacy features
interface CustomerPrivacySettings {
  customerId: string;
  emailConsent: boolean;
  marketingConsent: boolean;
  dataProcessingConsent: boolean;
  retentionPeriod: number; // Days
  lastConsentUpdate: Date;
  gdprRequests: PrivacyRequest[];
}

// Simple privacy request handling
type PrivacyRequestType = 'access' | 'rectification' | 'erasure' | 'portability';

interface PrivacyRequest {
  id: string;
  customerId: string;
  type: PrivacyRequestType;
  requestDate: Date;
  status: 'pending' | 'completed' | 'denied';
  responseDate?: Date;
}

// Basic data anonymization
function anonymizeCustomerData(customer: Customer): Customer {
  return {
    ...customer,
    name: 'Anonymous Customer',
    email: `deleted-${customer.id}@example.com`,
    phone: null,
    address: null,
    notes: '[Customer data anonymized per privacy request]'
  };
}
```

## Performance Considerations & Accessibility

### Essential Performance Features (YAGNI)
- **Pagination**: 50 customers per page with virtual scrolling
- **Lazy Loading**: Customer profiles load on selection
- **Search Debouncing**: 300ms delay on search input
- **Cached Analytics**: Customer metrics cached for 1 hour
- **Background Processing**: Heavy analytics calculated asynchronously

### Keyboard Navigation
- Tab through customer list and filters
- Enter to open customer profile
- Arrow keys for navigating customer cards
- Escape to close profile panels

### Screen Reader Support
- Customer counts and metrics announced
- Segment changes announced
- LTV and satisfaction scores read as text
- Communication status updates announced

### Visual Indicators
- Segment badges with colors and icons (⭐ 🆕 🔄 ⚠ 😴)
- Status indicators using shapes + colors
- Progress bars for lifecycle stages
- Communication health with color coding (green=good, yellow=needs attention, red=issues)