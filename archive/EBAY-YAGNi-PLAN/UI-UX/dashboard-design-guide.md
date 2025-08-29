# Dashboard UI/UX Design System Guide

## 1. Cấu trúc Layout

### 1.1 Grid System
```
┌─────────────────────────────────────────────────┐
│                    HEADER                       │
├────────────┬────────────────────────────────────┤
│            │                                    │
│  SIDEBAR   │         MAIN CONTENT AREA         │
│   (250px)  │         (Flexible width)          │
│            │                                    │
└────────────┴────────────────────────────────────┘
```

### 1.2 Responsive Breakpoints
- Desktop: ≥ 1280px
- Tablet: 768px - 1279px
- Mobile: < 768px (Sidebar collapse to hamburger menu)

## 2. Design Tokens

### 2.1 Colors
```css
/* Primary Colors */
--primary-blue: #5B8DEF;
--primary-blue-hover: #4A7FE5;

/* Status Colors */
--success-green: #22C55E;
--warning-yellow: #F59E0B;
--error-red: #EF4444;
--info-blue: #3B82F6;

/* Neutral Colors */
--gray-50: #F9FAFB;
--gray-100: #F3F4F6;
--gray-200: #E5E7EB;
--gray-300: #D1D5DB;
--gray-400: #9CA3AF;
--gray-500: #6B7280;
--gray-600: #4B5563;
--gray-700: #374151;
--gray-800: #1F2937;
--gray-900: #111827;

/* Background Colors */
--bg-primary: #FFFFFF;
--bg-secondary: #F8F9FC;
--bg-sidebar: #FFFFFF;
```

### 2.2 Typography
```css
/* Font Family */
--font-primary: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;

/* Font Sizes */
--text-xs: 12px;
--text-sm: 14px;
--text-base: 16px;
--text-lg: 18px;
--text-xl: 20px;
--text-2xl: 24px;
--text-3xl: 30px;
--text-4xl: 36px;

/* Font Weights */
--font-normal: 400;
--font-medium: 500;
--font-semibold: 600;
--font-bold: 700;

/* Line Heights */
--leading-tight: 1.25;
--leading-normal: 1.5;
--leading-relaxed: 1.75;
```

### 2.3 Spacing
```css
/* Spacing Scale */
--space-1: 4px;
--space-2: 8px;
--space-3: 12px;
--space-4: 16px;
--space-5: 20px;
--space-6: 24px;
--space-8: 32px;
--space-10: 40px;
--space-12: 48px;
--space-16: 64px;
```

### 2.4 Border & Shadow
```css
/* Border Radius */
--radius-sm: 4px;
--radius-base: 8px;
--radius-lg: 12px;
--radius-xl: 16px;
--radius-full: 9999px;

/* Shadows */
--shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
--shadow-base: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
--shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
--shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
```

## 3. Component Patterns

### 3.1 Header Component
```
┌─────────────────────────────────────────────────────────┐
│ [Logo] [Search Bar............] [🔔] [Language] [Avatar]│
└─────────────────────────────────────────────────────────┘
```
**Specifications:**
- Height: 64px
- Background: White
- Border-bottom: 1px solid --gray-200
- Padding: 0 24px
- Items aligned center with flexbox

### 3.2 Sidebar Navigation
```
┌──────────────┐
│ ✓ Dashboard  │ <- Active state
│ □ Products   │
│ □ Analytics  │
│ □ Reports    │
│              │
│ SECTION      │
│ □ Settings   │
│ □ Help       │
│ □ Logout     │
└──────────────┘
```
**Specifications:**
- Width: 250px (desktop), 280px (expanded)
- Background: White
- Item height: 44px
- Active state: Blue background with white text
- Hover state: Gray-100 background
- Icon size: 20px
- Text size: 14px

### 3.3 KPI Cards
```
┌─────────────────────────┐
│ [Icon]                  │
│ Label                   │
│ 12,345                  │
│ ↑ 12.5% from last month │
└─────────────────────────┘
```
**Specifications:**
- Min-width: 240px
- Padding: 24px
- Background: White
- Border-radius: 12px
- Shadow: --shadow-base
- Icon: 48px circle with light background
- Main number: 32px, font-weight: 700
- Label: 14px, color: --gray-500
- Trend: 12px with colored arrow (green/red)

### 3.4 Data Table
```
┌──────────────────────────────────────────┐
│ Column 1 ↓ │ Column 2 │ Column 3 │ Action│
├──────────────────────────────────────────┤
│ Data       │ Data     │ Data     │ [...] │
│ Data       │ Data     │ Data     │ [...] │
└──────────────────────────────────────────┘
```
**Specifications:**
- Background: White
- Border-radius: 12px
- Header: Gray-50 background, font-weight: 600
- Row height: 56px
- Hover state: Gray-50 background
- Border between rows: 1px solid --gray-100
- Pagination at bottom

### 3.5 Charts
**Line/Area Charts:**
- Height: 300-400px
- Grid lines: Dashed, --gray-200
- Primary color: --primary-blue
- Smooth curves with data points
- Tooltip on hover

**Bar/Column Charts:**
- Bar spacing: 8px
- Multiple series support
- Legend position: top-right
- Responsive scaling

### 3.6 Form Elements
**Input Fields:**
```
Label *
┌────────────────────┐
│ Placeholder text   │
└────────────────────┘
Helper text
```
- Height: 40px
- Border: 1px solid --gray-300
- Focus: Border --primary-blue
- Error state: Border --error-red

**Buttons:**
- Primary: Blue background, white text
- Secondary: White background, blue text, blue border
- Danger: Red background, white text
- Height: 40px (default), 32px (small), 48px (large)
- Border-radius: 8px
- Hover: Darken 10%

### 3.7 Modals & Overlays
```
┌─────────────────────────┐
│ Title              [X]  │
├─────────────────────────┤
│                         │
│     Content Area        │
│                         │
├─────────────────────────┤
│ [Cancel]    [Confirm]   │
└─────────────────────────┘
```
- Overlay: Black 50% opacity
- Modal background: White
- Border-radius: 16px
- Shadow: --shadow-xl
- Max-width: 600px (default)

## 4. Interactive States

### 4.1 Hover States
- Links: Underline or color change
- Buttons: Darken background 10%
- Cards: Elevate shadow to --shadow-md
- Table rows: Background --gray-50

### 4.2 Active/Selected States
- Navigation: Blue background, white text
- Tabs: Blue underline, blue text
- Checkboxes/Radio: Blue accent

### 4.3 Loading States
- Skeleton screens for content
- Spinner for actions
- Progress bars for uploads

### 4.4 Empty States
- Illustration/Icon
- Title: 20px, font-weight: 600
- Description: 14px, --gray-500
- CTA button

## 5. Accessibility Guidelines

### 5.1 Color Contrast
- Text on background: Minimum 4.5:1 ratio
- Large text: Minimum 3:1 ratio
- Interactive elements: Minimum 3:1 ratio

### 5.2 Focus Indicators
- Visible focus ring: 2px solid --primary-blue
- Keyboard navigation support
- Skip links for main content

### 5.3 ARIA Labels
- Proper labeling for screen readers
- Role attributes for custom components
- Descriptive alt text for images

## 6. Animation & Transitions

### 6.1 Timing Functions
```css
--ease-in: cubic-bezier(0.4, 0, 1, 1);
--ease-out: cubic-bezier(0, 0, 0.2, 1);
--ease-in-out: cubic-bezier(0.4, 0, 0.2, 1);
```

### 6.2 Duration
- Micro-interactions: 150ms
- Page transitions: 300ms
- Complex animations: 500ms

### 6.3 Common Animations
- Fade in/out
- Slide from right (modals)
- Scale (cards on hover)
- Skeleton loading

## 7. Implementation Examples

### 7.1 Sample Dashboard Layout
```html
<div class="dashboard-container">
  <header class="header">
    <!-- Header content -->
  </header>
  
  <aside class="sidebar">
    <!-- Navigation -->
  </aside>
  
  <main class="main-content">
    <div class="page-header">
      <h1>Dashboard Title</h1>
    </div>
    
    <div class="kpi-grid">
      <!-- KPI Cards -->
    </div>
    
    <div class="charts-section">
      <!-- Charts -->
    </div>
    
    <div class="table-section">
      <!-- Data Table -->
    </div>
  </main>
</div>
```

### 7.2 CSS Grid Layout
```css
.dashboard-container {
  display: grid;
  grid-template-columns: 250px 1fr;
  grid-template-rows: 64px 1fr;
  grid-template-areas:
    "header header"
    "sidebar main";
  height: 100vh;
}

.kpi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 24px;
}
```

## 8. Customization Guide

### 8.1 Áp dụng cho hệ thống khác
1. **Thay đổi màu chủ đạo**: Update biến --primary-blue
2. **Thay đổi font**: Update --font-primary
3. **Điều chỉnh spacing**: Modify spacing scale
4. **Custom components**: Giữ nguyên structure, thay đổi content

### 8.2 Ví dụ các hệ thống có thể áp dụng
- **E-commerce Dashboard**: Orders, Products, Revenue
- **HR Management**: Employees, Attendance, Payroll
- **Project Management**: Tasks, Timeline, Resources
- **IoT Monitoring**: Devices, Metrics, Alerts
- **Educational Platform**: Courses, Students, Grades

## 9. Best Practices

1. **Consistency**: Sử dụng design tokens nhất quán
2. **Hierarchy**: Phân cấp thông tin rõ ràng
3. **Whitespace**: Sử dụng khoảng trống hợp lý
4. **Feedback**: Cung cấp phản hồi cho user actions
5. **Performance**: Optimize images và lazy loading
6. **Responsive**: Test trên nhiều kích thước màn hình
7. **Accessibility**: Follow WCAG 2.1 guidelines

## 10. Resources & Tools

### Design Tools
- Figma/Sketch for mockups
- Adobe XD for prototypes
- Framer for interactions

### Development
- React/Vue/Angular for framework
- Tailwind CSS/Material-UI for styling
- Chart.js/D3.js for visualizations
- React Table/AG-Grid for data tables

### Icons & Assets
- Heroicons
- Feather Icons
- Phosphor Icons
- Unsplash/Pexels for images

---

*Note: File này cung cấp guidelines để thiết kế dashboard với style tương tự nhưng có thể áp dụng cho nhiều loại hệ thống khác nhau. Customize theo nhu cầu cụ thể của dự án.*