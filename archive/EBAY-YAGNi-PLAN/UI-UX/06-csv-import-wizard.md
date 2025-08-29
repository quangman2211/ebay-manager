# CSV Import Wizard - List-Based UI Design

## Design System Applied
- **Grid System**: 250px sidebar + flexible main content (following dashboard-design-guide.md)
- **Design Tokens**: Colors (#5B8DEF primary, status colors), Inter font, consistent spacing
- **Data Table Pattern**: 56px row height, sortable headers, hover states
- **Interactive States**: #F9FAFB hover, #5B8DEF selections, proper focus indicators

## SOLID/YAGNI Compliance
- **Single Responsibility**: File upload, validation, mapping, and processing are separate components
- **Open/Closed**: Import parser system extensible for new CSV formats without modifying existing parsers
- **Interface Segregation**: Separate interfaces for file handling, validation, data mapping, and import execution
- **Dependency Inversion**: Wizard depends on import service abstractions, not specific CSV parsing libraries
- **YAGNI**: Only essential import steps, no complex transformation rules until proven necessary

## Main CSV Import Wizard Layout (1280px+ Desktop)

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│ [Logo] eBay Manager Pro   [Search................] [🔔 3] [EN ▼] [Avatar ▼]     64px height      │
├────────────┬─────────────────────────────────────────────────────────────────────────────────────┤
│            │                                                                                      │
│  SIDEBAR   │                           CSV IMPORT WIZARD                                         │
│   250px    │                                                                                      │
│            │ ┌─ Page Header ──────────────────────────────────────────────────────────────────┐   │
│ □ Dashboard│ │ CSV Import Wizard                                     Account: Store1 ▼         │   │
│ □ Orders   │ │ Step 1 of 4: Select file and import type            [Help] [Templates] [History]│   │
│ □ Listings │ └────────────────────────────────────────────────────────────────────────────────┘   │
│ □ Products │                                                                                      │
│ □ Messages │ ┌─ Import Progress ───────────────────────────────────────────────────────────────┐   │
│ □ Customers│ │ ● Step 1: Select File → ○ Step 2: Map Columns → ○ Step 3: Validate → ○ Import  │   │
│ ✓Import    │ └────────────────────────────────────────────────────────────────────────────────┘   │
│            │                                                                                      │
│ TOOLS      │ ┌─ Import Type Selection ────────────────────────────────────────────────────────┐   │
│ □ Reports  │ │                                                                                │   │
│ □ Analytics│ │ Type                │ Description                          │ Sample Format   │   │   │
│ □ Settings │ ├────────────────────────────────────────────────────────────────────────────────┤   │
│            │ │ ● Orders           │ eBay order reports with buyer info   │ .csv, .xlsx     │   │   │
│ ACCOUNT    │ │                    │ • Sold orders & payment details     │ [Preview]       │   │   │
│ □ Profile  │ │                    │ • Customer contact information      │                 │   │   │
│ □ Billing  │ ├────────────────────────────────────────────────────────────────────────────────┤   │
│ □ Users    │ │ ○ Listings         │ eBay listing reports & performance   │ .csv, .xlsx     │   │   │
│ □ Help     │ │                    │ • Active & draft listings           │ [Preview]       │   │   │
│ □ Logout   │ │                    │ • Inventory & pricing data          │                 │   │   │
│            │ ├────────────────────────────────────────────────────────────────────────────────┤   │
│            │ │ ○ Products         │ Product catalog & supplier info     │ .csv, .xlsx     │   │   │
│            │ │                    │ • Inventory levels & pricing        │ [Preview]       │   │   │
│            │ │                    │ • Supplier & category data          │                 │   │   │
│            │ ├────────────────────────────────────────────────────────────────────────────────┤   │
│            │ │ ○ Messages         │ Customer communications & inquiries │ .csv, .txt      │   │   │
│            │ │                    │ • eBay message exports              │ [Preview]       │   │   │
│            │ │                    │ • Order-related communications     │                 │   │   │
│            │ └────────────────────────────────────────────────────────────────────────────────┘   │
│            │                                                                                      │
│            │ ┌─ File Upload Area ─────────────────────────────────────────────────────────────┐   │
│            │ │                                📁                                             │   │
│            │ │                      Drag & drop CSV file here                               │   │
│            │ │                         or click to browse                                   │   │
│            │ │                                                                              │   │
│            │ │             Supported: .csv, .xlsx, .tsv  •  Max size: 50MB                │   │
│            │ └────────────────────────────────────────────────────────────────────────────────┘   │
│            │                                                                                      │
│            │ ┌─ Recent Import History List ──────────────────────────────────────────────────┐   │
│            │ │                                                                              │   │
│            │ │ File Name                           │ Type     │ Records │ Date      │ Action│   │   │
│            │ ├──────────────────────────────────────────────────────────────────────────────┤   │
│            │ │ eBay-awaiting-shipment-report...    │ Orders   │ 156     │ 2h ago    │[Reuse]│   │   │
│            │ │ eBay-active-listings-report...      │ Listings │ 234     │ 1d ago    │[Reuse]│   │   │
│            │ │ products-inventory-update...        │ Products │ 89      │ 2d ago    │[Reuse]│   │   │
│            │ │ customer-messages-export...         │ Messages │ 45      │ 3d ago    │[Reuse]│   │   │
│            │ │                                                                              │   │
│            │ │ [View All History] [Download Templates] [Sample Files]                      │   │   │
│            │ └──────────────────────────────────────────────────────────────────────────────┘   │
│            │                                                                                      │
│            │ [Cancel] [Download Sample] [Next: Map Columns →]                                     │
└────────────┴─────────────────────────────────────────────────────────────────────────────────────┘
```

## Step 2: Column Mapping Interface

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│ [Logo] eBay Manager Pro   [Search................] [🔔 3] [EN ▼] [Avatar ▼]     64px height      │
├────────────┬─────────────────────────────────────────────────────────────────────────────────────┤
│            │                                                                                      │
│  SIDEBAR   │                           CSV IMPORT WIZARD                                         │
│   250px    │                                                                                      │
│            │ ┌─ Page Header ──────────────────────────────────────────────────────────────────┐   │
│ □ Dashboard│ │ Column Mapping                                        Account: Store1 ▼         │   │
│ □ Orders   │ │ Step 2 of 4: Map CSV columns to system fields      [Help] [Templates] [Reset]  │   │
│ □ Listings │ └────────────────────────────────────────────────────────────────────────────────┘   │
│ □ Products │                                                                                      │
│ □ Messages │ ┌─ Import Progress ───────────────────────────────────────────────────────────────┐   │
│ □ Customers│ │ ○ Step 1: Select File → ● Step 2: Map Columns → ○ Step 3: Validate → ○ Import  │   │
│ ✓Import    │ └────────────────────────────────────────────────────────────────────────────────┘   │
│            │                                                                                      │
│ TOOLS      │ ┌─ File Summary ─────────────────────────────────────────────────────────────────┐   │
│ □ Reports  │ │ eBay-awaiting-shipment-report-2025-08-24.csv │ 156 rows │ 78 cols │ 2.3 MB    │   │
│ □ Analytics│ │ Type: eBay Order Report (Auto-detected) │ Encoding: UTF-8 │ [Change Type]     │   │
│ □ Settings │ └────────────────────────────────────────────────────────────────────────────────┘   │
│            │                                                                                      │
│ ACCOUNT    │ ┌─ Mapping Summary List ─────────────────────────────────────────────────────────┐   │
│ □ Profile  │ │                                                                                │   │
│ □ Billing  │ │ Status              │ Count │ Action Required                                  │   │
│ □ Users    │ ├────────────────────────────────────────────────────────────────────────────────┤   │
│ □ Help     │ │ ✅ Auto-mapped     │ 67    │ [Review Mappings]                                │   │
│ □ Logout   │ │ ⚠ Unmapped         │ 11    │ [Map Remaining]                                  │   │
│            │ │ 🔄 Requires Review │ 3     │ [Review Conflicts]                               │   │
│            │ │ ❌ Invalid         │ 2     │ [Fix Invalid]                                    │   │
│            │ └────────────────────────────────────────────────────────────────────────────────┘   │
│            │                                                                                      │
│            │ ┌─ Column Mapping Data Table ───────────────────────────────────────────────────┐   │
│            │ │                                                                                │   │
│            │ │ CSV Column                   │ Sample Data          │ System Field       │ St │   │
│            │ ├────────────────────────────────────────────────────────────────────────────────┤   │
│            │ │ Sales Record Number          │ 239, 237, 235...     │ [Order ID ▼]       │ ✅ │   │
│            │ │ Order Number                 │ 18-13469-81867...    │ [Order Number ▼]   │ ✅ │   │
│            │ │ Buyer Username               │ marcelink-0...       │ [Cust Username ▼]  │ ✅ │   │
│            │ │ Buyer Name                   │ mark celinko...      │ [Customer Name ▼]  │ ✅ │   │
│            │ │ Buyer Email                  │ markcelinko@...      │ [Customer Email ▼] │ ✅ │   │
│            │ │ Item Number                  │ 357489760137...      │ [Item Number ▼]    │ ✅ │   │
│            │ │ Item Title                   │ Spider Farmer...     │ [Product Title ▼]  │ ✅ │   │
│            │ │ Custom Label                 │ SpiderFarmer...      │ [Select Field ▼]   │ ⚠  │   │
│            │ │ Total Price                  │ $96.23, $46.20...    │ [Order Total ▼]    │ ✅ │   │
│            │ │ eBay Collected Tax           │ $7.23, $4.20...      │ [Select Field ▼]   │ ⚠  │   │
│            │ │ Shipping Service             │ USPS Ground...       │ [Shipping Type ▼]  │ ✅ │   │
│            │ │ Ship To Name                 │ mark celinko...      │ [Ship Name ▼]      │ ✅ │   │
│            │ └────────────────────────────────────────────────────────────────────────────────┘   │
│            │                                                                                      │
│            │ ┌─ Bulk Mapping Actions ─────────────────────────────────────────────────────────┐   │
│            │ │ [Auto-Map All] [Map SKU Fields] [Map Tax Fields] [Ignore Unmapped] [Template]  │   │
│            │ └────────────────────────────────────────────────────────────────────────────────┘   │
│            │                                                                                      │
│            │ ┌─ Mapping Preview ──────────────────────────────────────────────────────────────┐   │
│            │ │                                                                                │   │
│            │ │ Order Number     │ Customer Name │ Product Title            │ SKU         │ Total│   │
│            │ ├────────────────────────────────────────────────────────────────────────────────┤   │
│            │ │ 18-13469-81867   │ mark celinko  │ Spider Farmer Controller │ SpiderFarmer│ $96  │   │
│            │ │ 21-13446-31215   │ Allison Price │ Harry Potter Phoenix     │ Scholastic  │ $46  │   │
│            │ │ 19-13445-28394   │ John Smith    │ Douay-Rheims Bible       │ Tanbooks    │ $42  │   │
│            │ │ 17-13444-15672   │ Sarah Johnson │ Cat Kid Comic Club       │ Scholastic  │ $43  │   │
│            │ │ 16-13443-09821   │ Mike Wilson   │ Heartstopper Box Set     │ Scholastic  │ $41  │   │
│            │ └────────────────────────────────────────────────────────────────────────────────┘   │
│            │                                                                                      │
│            │ [← Previous: Select File] [Preview Full Dataset] [Next: Validate Data →]              │
└────────────┴─────────────────────────────────────────────────────────────────────────────────────┘
```

## Step 3: Data Validation Interface

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│ [Logo] eBay Manager Pro   [Search................] [🔔 3] [EN ▼] [Avatar ▼]     64px height      │
├────────────┬─────────────────────────────────────────────────────────────────────────────────────┤
│            │                                                                                      │
│  SIDEBAR   │                           CSV IMPORT WIZARD                                         │
│   250px    │                                                                                      │
│            │ ┌─ Page Header ──────────────────────────────────────────────────────────────────┐   │
│ □ Dashboard│ │ Data Validation                                       Account: Store1 ▼         │   │
│ □ Orders   │ │ Step 3 of 4: Review data quality and fix issues    [Help] [Export] [Options]   │   │
│ □ Listings │ └────────────────────────────────────────────────────────────────────────────────┘   │
│ □ Products │                                                                                      │
│ □ Messages │ ┌─ Import Progress ───────────────────────────────────────────────────────────────┐   │
│ □ Customers│ │ ○ Step 1: Select File → ○ Step 2: Map Columns → ● Step 3: Validate → ○ Import  │   │
│ ✓Import    │ └────────────────────────────────────────────────────────────────────────────────┘   │
│            │                                                                                      │
│ TOOLS      │ ┌─ Validation Summary ───────────────────────────────────────────────────────────┐   │
│ □ Reports  │ │ Total: 156 │ ✅ Valid: 142 │ ⚠ Warnings: 12 │ ❌ Errors: 2 │ 📊 Duplicates: 3 │   │
│ □ Analytics│ │ Status: ⚠ Ready with Issues │ Action: Review errors and warnings               │   │
│ □ Settings │ └────────────────────────────────────────────────────────────────────────────────┘   │
│            │                                                                                      │
│ ACCOUNT    │ ┌─ Validation Issues List ───────────────────────────────────────────────────────┐   │
│ □ Profile  │ │                                                                                │   │
│ □ Billing  │ │ Type      │ Row │ Field          │ Issue Description           │ Action    │   │   │
│ □ Users    │ ├────────────────────────────────────────────────────────────────────────────────┤   │
│ □ Help     │ │ ❌ Error  │ 45  │ Order Number   │ Missing required field      │ [Fix][Skip]│   │   │
│ □ Logout   │ │ ❌ Error  │ 67  │ Customer Email │ Invalid format              │ [Fix][Skip]│   │   │
│            │ ├────────────────────────────────────────────────────────────────────────────────┤   │
│            │ │ ⚠ Warning │ 12  │ Phone Number   │ Inconsistent format         │ [Fix][OK] │   │   │
│            │ │ ⚠ Warning │ 23  │ Order Total    │ Unusually high: $2,456      │ [Review]  │   │   │
│            │ │ ⚠ Warning │ 34  │ Customer Email │ Anonymous eBay format       │ [Note][OK]│   │   │
│            │ │ ⚠ Warning │ 56  │ Product Title  │ Exceeds 200 chars           │ [Fix][OK] │   │   │
│            │ │ ⚠ Warning │ 78  │ State Code     │ Unrecognized: 'XX'          │ [Fix][OK] │   │   │
│            │ ├────────────────────────────────────────────────────────────────────────────────┤   │
│            │ │ 📊 Dup    │15,16│ Order Number   │ 18-13469-81867 multi-item   │ [Merge]   │   │   │
│            │ │ 📊 Dup    │23,89│ Order Number   │ 19-13445-28394 exact match  │ [Remove]  │   │   │
│            │ │ 📊 Dup    │34,35│ Customer Info  │ 17-13444-15672 similar      │ [Review]  │   │   │
│            │ └────────────────────────────────────────────────────────────────────────────────┘   │
│            │                                                                                      │
│            │ ┌─ Data Quality Report ──────────────────────────────────────────────────────────┐   │
│            │ │                                                                                │   │
│            │ │ Field               │ Complete │ Valid  │ Quality │ Notes                      │   │
│            │ ├────────────────────────────────────────────────────────────────────────────────┤   │
│            │ │ Order Number        │ 100% ✅  │ 98% ✅ │ Excellent│ 2 missing                  │   │
│            │ │ Customer Name       │ 99% ✅   │ 99% ✅ │ Excellent│ 1 empty                    │   │
│            │ │ Customer Email      │ 94% ⚠    │ 98% ✅ │ Good     │ 6% anonymous format       │   │
│            │ │ Product Title       │ 100% ✅  │ 92% ⚠  │ Good     │ 8% exceed length          │   │
│            │ │ Order Total         │ 100% ✅  │ 99% ✅ │ Excellent│ 1 unusual amount          │   │
│            │ │ Phone Numbers       │ 78% ⚠    │ 87% ⚠  │ Fair     │ Various formats           │   │
│            │ │ SKU/Custom Label    │ 87% ⚠    │ 95% ✅ │ Good     │ 13% missing               │   │
│            │ │ Tracking Numbers    │ 12% ❌   │ 100% ✅│ N/A      │ Expected for new orders   │   │
│            │ └────────────────────────────────────────────────────────────────────────────────┘   │
│            │                                                                                      │
│            │ ┌─ Import Configuration ─────────────────────────────────────────────────────────┐   │
│            │ │ Conflict Resolution: ● Update existing ○ Skip duplicates ○ Create new         │   │
│            │ │ Error Handling: ● Stop on errors ○ Skip error rows ○ Use placeholders        │   │
│            │ │ ☑ Email notification ☑ Backup existing data ☐ Test mode only                │   │
│            │ └────────────────────────────────────────────────────────────────────────────────┘   │
│            │                                                                                      │
│            │ [← Previous: Map Columns] [Fix All Errors] [Export Report] [Next: Import Data →]     │
└────────────┴─────────────────────────────────────────────────────────────────────────────────────┘
```

## Step 4: Import Execution & Progress

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│ [Logo] eBay Manager Pro   [Search................] [🔔 3] [EN ▼] [Avatar ▼]     64px height      │
├────────────┬─────────────────────────────────────────────────────────────────────────────────────┤
│            │                                                                                      │
│  SIDEBAR   │                           CSV IMPORT WIZARD                                         │
│   250px    │                                                                                      │
│            │ ┌─ Page Header ──────────────────────────────────────────────────────────────────┐   │
│ □ Dashboard│ │ Import Execution                                      Account: Store1 ▼         │   │
│ □ Orders   │ │ Step 4 of 4: Processing your data                   [Pause] [Cancel] [Log]     │   │
│ □ Listings │ └────────────────────────────────────────────────────────────────────────────────┘   │
│ □ Products │                                                                                      │
│ □ Messages │ ┌─ Import Progress ───────────────────────────────────────────────────────────────┐   │
│ □ Customers│ │ ○ Step 1: Select File → ○ Step 2: Map Columns → ○ Step 3: Validate → ● Import  │   │
│ ✓Import    │ └────────────────────────────────────────────────────────────────────────────────┘   │
│            │                                                                                      │
│ TOOLS      │ ┌─ Current Status ───────────────────────────────────────────────────────────────┐   │
│ □ Reports  │ │ File: eBay-awaiting-shipment-report-2025-08-24.csv                            │   │
│ □ Analytics│ │ Status: 🔄 Processing │ Started: 10:34 AM │ ETC: 10:37 AM │ 142/156 (91%)       │   │
│ □ Settings │ │ [████████████████████████████████████████████▓▓▓▓▓] 91%                       │   │
│            │ └────────────────────────────────────────────────────────────────────────────────┘   │
│ ACCOUNT    │                                                                                      │
│ □ Profile  │ ┌─ Processing Statistics ────────────────────────────────────────────────────────┐   │
│ □ Billing  │ │                                                                                │   │
│ □ Users    │ │ Metric              │ Count │ Value     │ Rate       │ Status              │   │   │
│ □ Help     │ ├────────────────────────────────────────────────────────────────────────────────┤   │
│ □ Logout   │ │ Total Records       │ 156   │ -         │ 2.3/sec    │ Processing          │   │   │
│            │ │ ✅ Successfully     │ 142   │ 91%       │ -          │ Completed           │   │   │
│            │ │ ⚠ Warnings          │ 12    │ 8%        │ -          │ Processed           │   │   │
│            │ │ ❌ Errors (Skipped) │ 2     │ 1%        │ -          │ Skipped             │   │   │
│            │ │ 🔄 Orders Created   │ 89    │ -         │ -          │ Database Updated    │   │   │
│            │ │ 🔄 Customers Added  │ 67    │ -         │ -          │ Database Updated    │   │   │
│            │ │ 🔄 Products Added   │ 23    │ -         │ -          │ Database Updated    │   │   │
│            │ │ 📊 Duplicates Fixed │ 3     │ -         │ -          │ Merged              │   │   │
│            │ └────────────────────────────────────────────────────────────────────────────────┘   │
│            │                                                                                      │
│            │ ┌─ Live Processing Log ──────────────────────────────────────────────────────────┐   │
│            │ │                                                                                │   │
│            │ │ Time     │ Action                                   │ Result              │   │   │
│            │ ├────────────────────────────────────────────────────────────────────────────────┤   │
│            │ │ 10:36:45 │ Processing record 142/156               │ Order 16-13443-09821│   │   │
│            │ │ 10:36:44 │ Created order: 17-13444-15672           │ ✅ Sarah Johnson    │   │   │
│            │ │ 10:36:43 │ Updated order: 18-13469-81867           │ ✅ Added tracking   │   │   │
│            │ │ 10:36:42 │ Created customer: Mike Wilson           │ ✅ mikew_comics     │   │   │
│            │ │ 10:36:41 │ Normalized phone for John Smith         │ ⚠ Format fixed     │   │   │
│            │ │ 10:36:40 │ Created order: 19-13445-28394           │ ✅ John Smith       │   │   │
│            │ │ 10:36:39 │ Skipped row 67                          │ ❌ Invalid email    │   │   │
│            │ │ 10:36:38 │ Merged order items: 18-13469-81867      │ ✅ Multi-item order │   │   │
│            │ │                                                    │ [Download Full Log] │   │   │
│            │ └────────────────────────────────────────────────────────────────────────────────┘   │
│            │                                                                                      │
│            │ ┌─ System Performance Monitor ───────────────────────────────────────────────────┐   │
│            │ │ Database: ████░░ 40% │ Memory: ███░░░ 30% │ CPU: ██░░░░ 25% │ Network: █░░░░░ 10% │   │
│            │ │ Status: ✅ Normal │ Performance: Good │ ETA: 45 seconds remaining               │   │
│            │ └────────────────────────────────────────────────────────────────────────────────┘   │
└────────────┴─────────────────────────────────────────────────────────────────────────────────────┘
```

## Import Completion & Summary

```
┌─ Import Complete! ──────────────────────────────────────────────────────────────────────────────────┐
│                                                                                                     │
│ ┌─ Import Summary ────────────────────────────────────────────────────────────────────────────────────┐ │
│ │                                                                                                   │ │
│ │ ✅ Import completed successfully!                                                                 │ │
│ │                                                                                                   │ │
│ │ File: eBay-awaiting-shipment-report-2025-08-24.csv                                               │ │
│ │ Started: 10:34:12 AM │ Completed: 10:37:45 AM │ Duration: 3m 33s                                │ │
│ │                                                                                                   │ │
│ └───────────────────────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                                     │
│ ┌─ Results Breakdown ─────────────────────────────────────────────────────────────────────────────────┐ │
│ │                                                                                                   │ │
│ │ ┌─ Processing Results ─────────────┐ ┌─ Database Changes ──────────────┐ ┌─ Data Quality ───────┐ │ │
│ │ │ Total Records:           156     │ │ ✅ Orders Created:      89      │ │ Success Rate: 96.2%  │ │ │
│ │ │ ✅ Successfully Imported: 150     │ │ ✅ Orders Updated:      34      │ │ Data Quality: 94.1%  │ │ │
│ │ │ ⚠ Processed with Warnings: 12    │ │ ✅ Customers Created:   67      │ │ Validation: 98.7%   │ │ │
│ │ │ ❌ Skipped (Errors):     2       │ │ ✅ Customers Updated:   12      │ │                     │ │ │
│ │ │ 🔄 Duplicates Handled:   3       │ │ ✅ Products Created:    23      │ │ [Quality Report]    │ │ │
│ │ │                                 │ │ 🔄 Background Tasks:    4 running│ │                     │ │ │
│ │ └─────────────────────────────────┘ └─────────────────────────────────┘ └─────────────────────┘ │ │
│ └───────────────────────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                                     │
│ ┌─ Issues Summary ────────────────────────────────────────────────────────────────────────────────────┐ │
│ │                                                                                                   │ │
│ │ ❌ Errors (2 records skipped):                                                                    │ │
│ │ • Row 45: Missing required Order Number - [Download Row] [Manual Fix]                           │ │
│ │ • Row 67: Invalid email format 'invalid@' - [Download Row] [Manual Fix]                         │ │
│ │                                                                                                   │ │
│ │ ⚠ Warnings (12 records processed with issues):                                                   │ │
│ │ • 8 phone number formats normalized                                                              │ │
│ │ • 3 product titles truncated (exceeded 200 chars)                                               │ │
│ │ • 1 state code corrected (XX → Unknown)                                                         │ │
│ │ [View All Warnings] [Download Warning Report]                                                   │ │
│ │                                                                                                   │ │
│ │ 🔄 Duplicate Handling:                                                                           │ │
│ │ • 1 order merged (multiple line items)                                                          │ │
│ │ • 2 exact duplicates removed                                                                     │ │
│ │ [View Duplicate Report]                                                                          │ │
│ │                                                                                                   │ │
│ └───────────────────────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                                     │
│ ┌─ Next Steps & Recommendations ─────────────────────────────────────────────────────────────────────┐ │
│ │                                                                                                   │ │
│ │ 🎯 Recommended Actions:                                                                          │ │
│ │ • Review and fix 2 error records for complete import                                            │ │
│ │ • Update 5 orders missing tracking numbers                                                      │ │
│ │ • Verify 3 high-value orders (>$500) for accuracy                                               │ │
│ │ • Complete background tasks: geocoding and profit calculations                                   │ │
│ │                                                                                                   │ │
│ │ 📊 Data Analysis Ready:                                                                          │ │
│ │ • 89 new orders available in Orders dashboard                                                   │ │
│ │ • 67 new customers available in Customer management                                              │ │
│ │ • 23 new products available in Product catalog                                                  │ │
│ │ • Updated inventory levels for existing products                                                 │ │
│ │                                                                                                   │ │
│ └───────────────────────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                                     │
│ ┌─ Actions ───────────────────────────────────────────────────────────────────────────────────────────┐ │
│ │ [📋 View Orders Dashboard] [👥 View Customers] [📦 View Products] [📧 Send Summary Email]        │ │
│ │                                                                                                   │ │
│ │ [📄 Download Full Report] [📈 Export Analytics] [🔄 Import Another File] [⚙️ Save Import Config]│ │
│ │                                                                                                   │ │
│ │ [🏠 Return to Dashboard] [📚 Import History] [❓ Help & Documentation]                           │ │
│ └───────────────────────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────────────────────┘
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

### Data Tables (Import Type, Column Mapping, Validation Issues)
- **Background**: #FFFFFF
- **Border-radius**: 12px
- **Shadow**: 0 1px 3px rgba(0,0,0,0.1)
- **Header**: #F8F9FC background, 14px, 600 weight
- **Row height**: 56px
- **Hover state**: #F9FAFB background
- **Selected row**: #EFF6FF background, #5B8DEF left border
- **Border between rows**: 1px solid #F3F4F6

### Status Indicators
- **Success**: ✅ #22C55E (success green)
- **Warning**: ⚠ #F59E0B (warning yellow)
- **Error**: ❌ #EF4444 (error red)
- **Processing**: 🔄 #3B82F6 (info blue)
- **Duplicate**: 📊 #8B5CF6 (purple)

## Mobile Layout (768px and below)

```
┌─────────────────────────────────────────┐
│ CSV Import      │ Store1 ▼ │ ☰ Menu    │
├─────────────────────────────────────────┤
│                                         │
│ ┌─ Progress ───────────────────────────┐ │
│ │ Step 1: File ● → 2: Map ○ → 3: Done │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ ┌─ Import Type ────────────────────────┐ │
│ │ What to import?                     │ │
│ │ ● Orders    ○ Listings              │ │
│ │ ○ Products  ○ Messages              │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ ┌─ File Upload ────────────────────────┐ │
│ │           📁                        │ │
│ │    Tap to select CSV file           │ │
│ │    or drag & drop                   │ │
│ │                                     │ │
│ │ Max 50MB • .csv, .xlsx, .tsv       │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ ┌─ Recent Imports ─────────────────────┐ │
│ │ • Orders (156) - 2h ago             │ │
│ │ • Listings (234) - 1d ago           │ │
│ │ • Products (89) - 2d ago            │ │
│ │ [View History]                      │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ [Sample Files] [Next Step →]            │
└─────────────────────────────────────────┘
```

## SOLID Component Architecture

### CSV Import Components (Single Responsibility)
```typescript
// Main import wizard container
interface CSVImportWizardProps {
  currentAccount: Account;
  onImportComplete: (result: ImportResult) => void;
}

<CSVImportWizard>
  <ImportStepProgress currentStep={currentStep} />
  <FileUploader onFileSelected={handleFileSelection} />
  <ColumnMapper csvColumns={csvColumns} systemFields={systemFields} />
  <DataValidator mappedData={mappedData} />
  <ImportProcessor validatedData={validatedData} />
  <ImportSummary importResult={importResult} />
</CSVImportWizard>

// Individual wizard steps with specific responsibilities
<FileUploader>           // Only handles file selection and basic validation
<ColumnMapper>           // Only handles CSV column to system field mapping
<DataValidator>          // Only validates mapped data quality and integrity
<ImportProcessor>        // Only executes the actual data import
<ImportSummary>          // Only displays import results and recommendations
<ProgressTracker>        // Only tracks and displays import progress
```

### Interface Segregation Examples
```typescript
// File handling interface
interface FileHandler {
  uploadFile: (file: File) => Promise<FileInfo>;
  validateFileFormat: (file: File) => Promise<FormatValidation>;
  parseCSVHeaders: (file: File) => Promise<string[]>;
  previewCSVData: (file: File, rows: number) => Promise<any[]>;
}

// Column mapping interface (separate from file handling)
interface ColumnMapper {
  detectMappings: (csvHeaders: string[], importType: ImportType) => Promise<ColumnMapping[]>;
  applyMapping: (csvData: any[], mapping: ColumnMapping[]) => Promise<MappedData[]>;
  saveTemplate: (mapping: ColumnMapping[], name: string) => Promise<void>;
  loadTemplate: (templateId: string) => Promise<ColumnMapping[]>;
}

// Data validation interface (separate from mapping)
interface DataValidator {
  validateData: (mappedData: MappedData[]) => Promise<ValidationResult>;
  checkDuplicates: (data: MappedData[]) => Promise<DuplicateReport>;
  validateFields: (data: MappedData[], rules: ValidationRule[]) => Promise<FieldValidation[]>;
  generateQualityReport: (data: MappedData[]) => Promise<QualityReport>;
}

// Import execution interface (separate from validation)
interface ImportExecutor {
  startImport: (validatedData: ValidatedData[], options: ImportOptions) => Promise<void>;
  pauseImport: () => Promise<void>;
  cancelImport: () => Promise<void>;
  getImportStatus: () => Promise<ImportStatus>;
  onProgressUpdate: (callback: (progress: ImportProgress) => void) => void;
}
```

## Mobile Layout (768px and below)

```
┌─────────────────────────────────────────┐
│ CSV Import      │ Store1 ▼ │ ☰ Menu    │
├─────────────────────────────────────────┤
│                                         │
│ ┌─ Progress ───────────────────────────┐ │
│ │ Step 1: File ● → 2: Map ○ → 3: Done │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ ┌─ Import Type ────────────────────────┐ │
│ │ What to import?                     │ │
│ │ ● Orders    ○ Listings              │ │
│ │ ○ Products  ○ Messages              │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ ┌─ File Upload ────────────────────────┐ │
│ │           📁                        │ │
│ │    Tap to select CSV file           │ │
│ │    or drag & drop                   │ │
│ │                                     │ │
│ │ Max 50MB • .csv, .xlsx, .tsv       │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ ┌─ Recent Imports ─────────────────────┐ │
│ │ • Orders (156) - 2h ago             │ │
│ │ • Listings (234) - 1d ago           │ │
│ │ • Products (89) - 2d ago            │ │
│ │ [View History]                      │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ [Sample Files] [Next Step →]            │
└─────────────────────────────────────────┘
```

## Import Type Detection System (YAGNI)

```typescript
// Simple file type detection based on headers and content patterns
interface ImportTypeDetector {
  detectImportType: (csvHeaders: string[], sampleData: any[]) => ImportType;
  getConfidenceScore: (importType: ImportType, csvHeaders: string[]) => number;
}

// Rule-based detection (no complex ML)
function detectImportType(csvHeaders: string[], sampleData: any[]): ImportType {
  const headers = csvHeaders.map(h => h.toLowerCase());
  
  // eBay Order Report detection
  const orderHeaders = ['sales record number', 'order number', 'buyer username', 'buyer name'];
  if (orderHeaders.every(h => headers.some(header => header.includes(h)))) {
    return 'ebay_orders';
  }
  
  // eBay Listing Report detection  
  const listingHeaders = ['item number', 'title', 'available quantity', 'start price'];
  if (listingHeaders.every(h => headers.some(header => header.includes(h)))) {
    return 'ebay_listings';
  }
  
  // Product/Inventory detection
  const productHeaders = ['sku', 'product name', 'price', 'quantity', 'supplier'];
  if (productHeaders.filter(h => headers.some(header => header.includes(h))).length >= 3) {
    return 'products';
  }
  
  // Message/Communication detection
  const messageHeaders = ['from', 'to', 'subject', 'message', 'date'];
  if (messageHeaders.filter(h => headers.some(header => header.includes(h))).length >= 3) {
    return 'messages';
  }
  
  return 'unknown';
}

// Pre-defined field mappings for known formats
const FIELD_MAPPINGS: Record<ImportType, ColumnMapping[]> = {
  ebay_orders: [
    { csvColumn: 'Sales Record Number', systemField: 'sales_record_id', required: false },
    { csvColumn: 'Order Number', systemField: 'order_number', required: true },
    { csvColumn: 'Buyer Username', systemField: 'customer_username', required: true },
    { csvColumn: 'Buyer Name', systemField: 'customer_name', required: true },
    { csvColumn: 'Buyer Email', systemField: 'customer_email', required: true },
    { csvColumn: 'Item Number', systemField: 'item_number', required: true },
    { csvColumn: 'Item Title', systemField: 'product_title', required: true },
    { csvColumn: 'Custom Label', systemField: 'product_sku', required: false },
    { csvColumn: 'Total Price', systemField: 'order_total', required: true },
    { csvColumn: 'Quantity', systemField: 'quantity', required: true },
    { csvColumn: 'Sale Date', systemField: 'order_date', required: true },
    { csvColumn: 'Payment Method', systemField: 'payment_method', required: false },
    { csvColumn: 'Shipping Service', systemField: 'shipping_service', required: false },
    { csvColumn: 'Tracking Number', systemField: 'tracking_number', required: false }
  ],
  
  ebay_listings: [
    { csvColumn: 'Item number', systemField: 'item_number', required: true },
    { csvColumn: 'Title', systemField: 'listing_title', required: true },
    { csvColumn: 'Custom label (SKU)', systemField: 'sku', required: false },
    { csvColumn: 'Available quantity', systemField: 'quantity', required: true },
    { csvColumn: 'Start price', systemField: 'price', required: true },
    { csvColumn: 'Sold quantity', systemField: 'sold_quantity', required: false },
    { csvColumn: 'Watchers', systemField: 'watchers', required: false },
    { csvColumn: 'Start date', systemField: 'start_date', required: true },
    { csvColumn: 'End date', systemField: 'end_date', required: true },
    { csvColumn: 'eBay category 1 name', systemField: 'category', required: false },
    { csvColumn: 'Condition', systemField: 'condition', required: true }
  ]
};
```

## Data Validation Rules Engine

```typescript
// Simple validation rules system
interface ValidationRule {
  field: string;
  type: 'required' | 'format' | 'range' | 'unique' | 'custom';
  parameters: any;
  errorMessage: string;
  warningMessage?: string;
}

// Pre-defined validation rules for different data types
const VALIDATION_RULES: Record<string, ValidationRule[]> = {
  order_number: [
    {
      field: 'order_number',
      type: 'required',
      parameters: {},
      errorMessage: 'Order number is required'
    },
    {
      field: 'order_number', 
      type: 'format',
      parameters: { pattern: /^\d{2}-\d{5}-\d{5}$/ },
      errorMessage: 'Order number must be in format XX-XXXXX-XXXXX',
      warningMessage: 'Order number format is unusual'
    }
  ],
  
  customer_email: [
    {
      field: 'customer_email',
      type: 'required',
      parameters: {},
      errorMessage: 'Customer email is required'
    },
    {
      field: 'customer_email',
      type: 'format', 
      parameters: { pattern: /^[^\s@]+@[^\s@]+\.[^\s@]+$/ },
      errorMessage: 'Invalid email format',
      warningMessage: 'Email format is unusual'
    }
  ],
  
  order_total: [
    {
      field: 'order_total',
      type: 'required',
      parameters: {},
      errorMessage: 'Order total is required'
    },
    {
      field: 'order_total',
      type: 'range',
      parameters: { min: 0.01, max: 10000 },
      errorMessage: 'Order total must be between $0.01 and $10,000',
      warningMessage: 'Order total is unusually high'
    }
  ]
};

// Simple validation executor
class DataValidator {
  validateRecord(record: any, rules: ValidationRule[]): ValidationResult {
    const errors: ValidationError[] = [];
    const warnings: ValidationWarning[] = [];
    
    for (const rule of rules) {
      const value = record[rule.field];
      const result = this.applyRule(value, rule);
      
      if (result.error) {
        errors.push({
          field: rule.field,
          message: rule.errorMessage,
          value: value,
          rule: rule.type
        });
      } else if (result.warning) {
        warnings.push({
          field: rule.field,
          message: rule.warningMessage || 'Unusual value detected',
          value: value,
          rule: rule.type
        });
      }
    }
    
    return {
      isValid: errors.length === 0,
      errors,
      warnings
    };
  }
  
  private applyRule(value: any, rule: ValidationRule): { error: boolean, warning: boolean } {
    switch (rule.type) {
      case 'required':
        return { error: !value || value === '', warning: false };
        
      case 'format':
        const isValid = rule.parameters.pattern.test(value?.toString() || '');
        return { error: !isValid && rule.errorMessage, warning: !isValid && rule.warningMessage };
        
      case 'range':
        const numValue = Number(value);
        const inRange = numValue >= rule.parameters.min && numValue <= rule.parameters.max;
        const isWarning = numValue > rule.parameters.max * 0.8; // 80% threshold for warning
        return { error: !inRange, warning: isWarning && inRange };
        
      default:
        return { error: false, warning: false };
    }
  }
}
```

## Progress Tracking System (Real-time Updates)

```typescript
// Simple progress tracking with WebSocket updates
interface ImportProgress {
  totalRecords: number;
  processedRecords: number;
  successfulRecords: number;
  warningRecords: number;
  errorRecords: number;
  currentRecord: any;
  startTime: Date;
  estimatedCompletion: Date;
  status: ImportStatus;
  messages: ImportMessage[];
}

class ImportProgressTracker {
  private progress: ImportProgress;
  private callbacks: ((progress: ImportProgress) => void)[] = [];
  
  updateProgress(update: Partial<ImportProgress>) {
    this.progress = { ...this.progress, ...update };
    
    // Calculate derived metrics
    this.progress.estimatedCompletion = this.calculateETA();
    
    // Notify all subscribers
    this.callbacks.forEach(callback => callback(this.progress));
  }
  
  addProgressListener(callback: (progress: ImportProgress) => void) {
    this.callbacks.push(callback);
  }
  
  private calculateETA(): Date {
    const elapsed = Date.now() - this.progress.startTime.getTime();
    const rate = this.progress.processedRecords / (elapsed / 1000); // records per second
    const remaining = this.progress.totalRecords - this.progress.processedRecords;
    const secondsRemaining = remaining / rate;
    
    return new Date(Date.now() + secondsRemaining * 1000);
  }
}
```

## Error Handling & Recovery (YAGNI)

```typescript
// Simple error categorization and handling
type ImportErrorType = 'validation' | 'database' | 'network' | 'permission' | 'system';

interface ImportError {
  id: string;
  type: ImportErrorType;
  row: number;
  field?: string;
  message: string;
  originalValue?: any;
  suggestedFix?: string;
  canRetry: boolean;
  canSkip: boolean;
}

class ImportErrorHandler {
  handleError(error: ImportError, options: ImportOptions): ImportErrorAction {
    switch (options.errorHandling) {
      case 'stop_on_error':
        return { action: 'stop', message: `Import stopped due to error: ${error.message}` };
        
      case 'skip_errors':
        if (error.canSkip) {
          return { action: 'skip', message: `Skipped row ${error.row}: ${error.message}` };
        } else {
          return { action: 'stop', message: `Cannot skip critical error: ${error.message}` };
        }
        
      case 'use_defaults':
        if (error.type === 'validation' && error.suggestedFix) {
          return { action: 'fix', value: error.suggestedFix, message: `Applied fix: ${error.suggestedFix}` };
        } else {
          return { action: 'skip', message: `No fix available, skipping row ${error.row}` };
        }
        
      default:
        return { action: 'stop', message: 'Unknown error handling option' };
    }
  }
}
```

## Import Templates & Configuration

```typescript
// Reusable import configurations
interface ImportTemplate {
  id: string;
  name: string;
  importType: ImportType;
  columnMappings: ColumnMapping[];
  validationRules: ValidationRule[];
  importOptions: ImportOptions;
  createdBy: string;
  createdDate: Date;
  usageCount: number;
}

class ImportTemplateManager {
  private templates: Map<string, ImportTemplate> = new Map();
  
  saveTemplate(template: Omit<ImportTemplate, 'id' | 'createdDate' | 'usageCount'>): string {
    const id = `tpl_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    const fullTemplate: ImportTemplate = {
      ...template,
      id,
      createdDate: new Date(),
      usageCount: 0
    };
    
    this.templates.set(id, fullTemplate);
    return id;
  }
  
  applyTemplate(templateId: string, csvHeaders: string[]): ImportConfiguration {
    const template = this.templates.get(templateId);
    if (!template) {
      throw new Error(`Template ${templateId} not found`);
    }
    
    // Auto-adjust mappings based on actual CSV headers
    const adjustedMappings = template.columnMappings
      .map(mapping => ({
        ...mapping,
        found: csvHeaders.includes(mapping.csvColumn)
      }))
      .filter(mapping => mapping.found || !mapping.required);
    
    template.usageCount++;
    
    return {
      importType: template.importType,
      columnMappings: adjustedMappings,
      validationRules: template.validationRules,
      importOptions: template.importOptions
    };
  }
}
```

## Accessibility & Performance

### Keyboard Navigation
- Tab through all wizard steps and form fields
- Enter/Space to select files and confirm actions
- Arrow keys for navigating validation issues
- Escape to cancel import or close dialogs

### Screen Reader Support
- Progress announcements during import
- Error and warning counts announced
- Step completion announced
- File upload status announced

### Visual Indicators
- Progress bars with percentage text
- Color-coded status indicators (✅ ⚠ ❌)
- Real-time log messages with timestamps
- System performance monitors

### Performance Considerations (YAGNI)
- **Chunked Processing**: Process 100 records at a time to avoid memory issues
- **Background Tasks**: Run non-critical tasks (geocoding, emails) in background
- **Progress Streaming**: Use WebSockets for real-time progress updates
- **Memory Management**: Clear processed data from memory to prevent leaks
- **Pause/Resume**: Allow pausing large imports without losing progress

No premature optimizations - these are the minimal essential performance features needed for reliable CSV import of the expected data volumes (hundreds to low thousands of records).