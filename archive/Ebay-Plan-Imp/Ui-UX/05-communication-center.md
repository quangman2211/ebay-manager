# Communication Center - List-Based UI Design

## Design System Applied
- **Grid System**: 250px sidebar + flexible main content (following dashboard-design-guide.md)
- **Design Tokens**: Colors (#5B8DEF primary, status colors), Inter font, consistent spacing
- **Data Table Pattern**: 56px row height, sortable headers, hover states
- **Interactive States**: #F9FAFB hover, #5B8DEF selections, proper focus indicators

## SOLID/YAGNI Compliance
- **Single Responsibility**: Inbox view, message composer, templates, and automation are separate components
- **Open/Closed**: Template system extensible without modifying inbox or composer
- **Interface Segregation**: Separate interfaces for message display, composition, templates, and automation
- **Dependency Inversion**: Components depend on message service abstractions, not Gmail/eBay APIs directly
- **YAGNI**: Only essential communication features, no advanced AI or complex automation initially

## Main Communication Center Layout (1280px+ Desktop)

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│ [Logo] eBay Manager Pro   [Search................] [🔔 3] [EN ▼] [Avatar ▼]     64px height      │
├────────────┬─────────────────────────────────────────────────────────────────────────────────────┤
│            │                                                                                      │
│  SIDEBAR   │                       COMMUNICATION CENTER                                           │
│   250px    │                                                                                      │
│            │ ┌─ Page Header ──────────────────────────────────────────────────────────────────┐   │
│ □ Dashboard│ │ Communication Center                                  Account: Store1 ▼         │   │
│ □ Orders   │ │ 12 unread, 23 today, 2.3h avg response           [Sync] [Compose] [Settings]  │   │
│ □ Listings │ └────────────────────────────────────────────────────────────────────────────────┘   │
│ □ Products │                                                                                      │
│ ✓Messages  │ ┌─ Message Summary List ─────────────────────────────────────────────────────────┐   │
│ □ Customers│ │                                                                                │   │
│ □ Import   │ │ Status          │ Count │ Avg Response │ Source     │ Action Required        │   │
│            │ ├────────────────────────────────────────────────────────────────────────────────┤   │
│ TOOLS      │ │ 📥 Unread       │ 12    │ 0h          │ Mixed      │ [Reply Now]            │   │
│ □ Reports  │ │ ⚠ Urgent        │ 3     │ 1.2h        │ eBay       │ [Urgent Reply]         │   │
│ □ Analytics│ │ ✉️ Today        │ 23    │ 2.3h        │ All        │ [View Today]           │   │
│ □ Settings │ │ 📤 Sent Today   │ 15    │ -           │ All        │ [View Sent]            │   │
│            │ │ 🔄 Follow-ups   │ 5     │ 24h         │ Auto       │ [Process Queue]        │   │
│ ACCOUNT    │ └────────────────────────────────────────────────────────────────────────────────┘   │
│ □ Profile  │                                                                                      │
│ □ Billing  │ ┌─ Search & Filters ─────────────────────────────────────────────────────────────┐   │
│ □ Users    │ │                                                                                │   │
│ □ Help     │ │ Search: [Subject, sender, order#...............] [🔍] [Clear] [Save]          │   │
│ □ Logout   │ │                                                                                │   │
│            │ │ Source: [All ▼] Status: [All ▼] Date: [All ▼] Priority: [All ▼]               │   │
│            │ │                                                                                │   │
│            │ │ Quick Filters:                                                                 │   │
│            │ │ [Unread] [Urgent] [Orders] [Returns] [Today] [This Week] [Needs Reply]        │   │
│            │ └────────────────────────────────────────────────────────────────────────────────┘   │
│            │                                                                                      │
│            │ ┌─ Bulk Actions ─────────────────────────────────────────────────────────────────┐   │
│            │ │ Selected: 0 │ [Select All] [Select Filtered] [Clear Selection]                │   │
│            │ │ [Mark Read] [Archive] [Apply Template] [Bulk Reply] [Forward] [Delete]         │   │
│            │ └────────────────────────────────────────────────────────────────────────────────┘   │
│            │                                                                                      │
│            │ ┌─ Message Data Table ───────────────────────────────────────────────────────────┐   │
│            │ │                                                                                │   │
│            │ │ ☐ │ From ↓        │ Subject             │Date│Order   │Src│St│Reply│Actions     │ │
│            │ ├───────────────────────────────────────────────────────────────────────────────────┤   │
│            │ │ ☐ │ mark celinko  │ ⚠ Question about   │2h  │18-13469│📧 │ ● │⏰  │[Reply][••] │ │
│            │ │   │ marcelink-0   │ Spider Farmer       │ago │-81867  │   │   │    │            │ │
│            │ ├───────────────────────────────────────────────────────────────────────────────────┤   │
│            │ │ ☐ │ Allison Price │ ✅ Delivery        │4h  │21-13446│📧 │ ✓ │✓  │[View][••]  │ │
│            │ │   │ ammart05      │ confirmation        │ago │-31215  │   │   │    │            │ │
│            │ ├───────────────────────────────────────────────────────────────────────────────────┤   │
│            │ │ ☐ │ John Smith    │ 💰 Payment         │1d  │19-13445│📧 │ ● │⚠  │[Reply][••] │ │
│            │ │   │ bookworm123   │ question            │ago │-28394  │   │   │    │            │ │
│            │ ├───────────────────────────────────────────────────────────────────────────────────┤   │
│            │ │ ☐ │ Sarah Johnson │ 📦 When will my    │2d  │17-13444│📧 │ ● │⏰  │[Reply][••] │ │
│            │ │   │ sarahj_reads  │ comics ship?        │ago │-15672  │   │   │    │            │ │
│            │ └───────────────────────────────────────────────────────────────────────────────────┘   │
│            │                                                                                      │
│            │ ┌─ Message Details Panel (Expandable) ──────────────────────────────────────────────┐   │
│            │ │ From: mark celinko (marcelink-0) │ Order: 18-13469-81867 │ [Close ×]            │   │
│            │ ├──────────────────────────────────────────────────────────────────────────────────┤   │
│            │ │ Subject: Question about Spider Farmer shipment │ eBay │ 2h ago │ Urgent Reply   │   │
│            │ │ Order Status: Need Tracking │ Payment: ✓ Paid │ Ship By: Sep-01 │ Days: 3     │   │
│            │ │ Message: "I ordered the Spider Farmer GGS Controller on Aug 21st..."              │   │
│            │ │                                                                              │   │
│            │ │ [Quick Reply] [Use Template] [Mark Resolved] [Add Note] [View Order]         │   │
│            │ └──────────────────────────────────────────────────────────────────────────────────┘   │
│            │                                                                                      │
│            │ ┌─ Pagination ───────────────────────────────────────────────────────────────────┐   │
│            │ │ 1-20 of 127 messages │ [◀] [1] [2] [3] ... [7] [▶] │ 20 per page [▼]        │   │
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

### Data Table (Message List)
- **Background**: #FFFFFF
