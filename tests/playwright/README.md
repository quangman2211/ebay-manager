# eBay Manager - Playwright Testing Suite

Comprehensive end-to-end testing with visual validation for the eBay Manager application.

## 🎯 Overview

This testing suite provides complete coverage of both frontend UI components and backend API functionality using Playwright with visual screenshots and performance metrics.

## 📁 Test Structure

```
tests/playwright/
├── tests/
│   ├── backend-api.spec.ts          # API endpoint testing with visual docs
│   ├── frontend-ui.spec.ts          # UI component testing with screenshots
│   ├── e2e-workflows.spec.ts        # Complete user journey testing
│   ├── visual-regression.spec.ts    # Visual baselines and performance
│   ├── fixtures/
│   │   └── test-data.ts             # Test data and configuration
│   └── utils/
│       └── api-helpers.ts           # API testing utilities
├── playwright.config.ts             # Playwright configuration
├── run-tests.sh                     # Test execution script
├── generate-report.js               # HTML report generator
└── README.md                        # This file
```

## 🚀 Quick Start

### Prerequisites

1. **Application Running**: Ensure both backend (port 8000) and frontend (port 3000) are running:
   ```bash
   cd /path/to/ebay-manager
   ./start-app.sh
   ```

2. **Node.js**: Version 14 or higher

### Running Tests

#### Option 1: Automated Script (Recommended)
```bash
cd tests/playwright
./run-tests.sh
```

#### Option 2: Manual Execution
```bash
cd tests/playwright
npm install
npx playwright install
npx playwright test
```

#### Option 3: Interactive Mode
```bash
npx playwright test --ui
```

## 📋 Test Suites

### 1. Backend API Testing (`backend-api.spec.ts`)
- **API Documentation**: Screenshots of FastAPI docs interface
- **Authentication**: Login endpoints and token validation  
- **Account Management**: CRUD operations for eBay accounts
- **CSV Upload**: File upload functionality with validation
- **Order Management**: Order CRUD and status updates
- **Listings**: Listing retrieval and management
- **Performance**: API response time validation
- **Error Handling**: Invalid requests and edge cases

**Key Screenshots:**
- `api-docs-full.png` - Complete API documentation
- `api-auth-endpoints.png` - Authentication endpoints
- `api-orders-endpoints.png` - Order management APIs

### 2. Frontend UI Testing (`frontend-ui.spec.ts`)
- **Login Page**: Form validation and authentication flow
- **Dashboard**: Statistics cards and data visualization
- **Orders Page**: Data grid, filtering, and status management
- **Listings Page**: Search functionality and listing display
- **CSV Upload**: Drag-and-drop interface and file handling
- **Navigation**: Menu functionality and routing
- **Responsive Design**: Mobile, tablet, and desktop layouts
- **Accessibility**: Keyboard navigation and screen reader support

**Key Screenshots:**
- `login-page-*.png` - Login form states
- `dashboard-*.png` - Dashboard components
- `orders-*.png` - Order management interface
- `listings-*.png` - Listing management interface
- `csv-upload-*.png` - File upload interface

### 3. End-to-End Workflows (`e2e-workflows.spec.ts`)
- **Complete User Journey**: Login → Dashboard → Upload → Orders → Listings
- **CSV Processing Workflow**: Upload → Process → View → Update
- **Multi-Account Testing**: Admin vs staff permissions
- **Responsive Workflow**: Cross-device user experience
- **Error Recovery**: Network failure handling and recovery
- **Performance Testing**: Page load times and user interactions
- **Data Lifecycle**: Complete CRUD operations with validation

**Key Screenshots:**
- `e2e-01-login-start.png` through `e2e-13-final-dashboard-state.png`
- `e2e-csv-workflow-*.png` - Complete upload workflow
- `e2e-responsive-*.png` - Multi-device testing

### 4. Visual Regression & Performance (`visual-regression.spec.ts`)
- **Visual Baselines**: Component-level screenshot comparison
- **Cross-Browser Testing**: Chrome, Firefox, Safari consistency
- **Performance Metrics**: Page load times and resource usage
- **Memory Testing**: JavaScript heap usage monitoring
- **Mobile Performance**: Network throttling and mobile optimization
- **Accessibility Testing**: Color contrast and keyboard navigation

**Key Screenshots:**
- `visual-baseline-*.png` - Component baseline captures
- `accessibility-*.png` - Accessibility testing results
- `visual-cross-browser-*.png` - Browser consistency testing

## 📊 Test Results

### Screenshot Organization
Screenshots are automatically organized by category:

- **API Testing** (`api-*`): Backend API documentation and functionality
- **Authentication** (`login-*`): Login process and security
- **Dashboard** (`dashboard-*`): Main dashboard interface
- **Order Management** (`orders-*`): Order processing workflow
- **Listing Management** (`listings-*`): Product listing interface
- **CSV Upload** (`upload-*`): File processing interface
- **End-to-End** (`e2e-*`): Complete user journeys
- **Visual Baselines** (`visual-baseline-*`): Component baselines
- **Responsive Design** (`responsive-*`): Multi-device layouts
- **Accessibility** (`accessibility-*`): Accessibility compliance

### Performance Metrics
The tests monitor and validate:
- Page load times (< 4 seconds)
- API response times (< 2 seconds)
- Authentication speed (< 1 second)
- Memory usage (< 100MB JavaScript heap)
- Network request efficiency
- Resource loading optimization

### Report Generation
After test execution:

1. **Playwright HTML Report**: 
   ```bash
   npx playwright show-report
   ```

2. **Custom Visual Report**:
   ```bash
   node generate-report.js
   open test-report.html
   ```

## 🛠 Configuration

### Browser Settings
```typescript
// playwright.config.ts
projects: [
  { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  { name: 'firefox', use: { ...devices['Desktop Firefox'] } },
  { name: 'webkit', use: { ...devices['Desktop Safari'] } },
  { name: 'Mobile Chrome', use: { ...devices['Pixel 5'] } },
  { name: 'Mobile Safari', use: { ...devices['iPhone 12'] } }
]
```

### Test Data
```typescript
// fixtures/test-data.ts
export const testCredentials = {
  admin: { username: 'admin', password: 'admin123' },
  staff: { username: 'staff', password: 'staff123' }
};
```

### Screenshot Settings
- **Full Page**: Complete page captures for layout validation
- **Component Level**: Individual component screenshots
- **Animation Disabled**: Consistent visual regression testing
- **High Resolution**: Detailed visual validation

## 🔍 Debugging

### Debug Mode
```bash
npx playwright test --debug
```

### Headed Mode (Watch Tests Run)
```bash
npx playwright test --headed
```

### Specific Test
```bash
npx playwright test tests/frontend-ui.spec.ts
```

### Trace Viewer
```bash
npx playwright show-trace trace.zip
```

## 📈 Coverage

### Frontend Coverage
- ✅ All React components (Login, Dashboard, Orders, Listings, Upload)
- ✅ All user interactions (clicks, form inputs, navigation)
- ✅ All responsive breakpoints (mobile, tablet, desktop)
- ✅ All error states and edge cases
- ✅ All accessibility features

### Backend Coverage
- ✅ All API endpoints (`/login`, `/accounts`, `/orders`, `/listings`, `/csv/upload`)
- ✅ All HTTP methods (GET, POST, PUT, DELETE)
- ✅ All authentication flows
- ✅ All error responses and status codes
- ✅ All data processing workflows

### Cross-Browser Coverage
- ✅ Chrome/Chromium
- ✅ Firefox
- ✅ Safari/Webkit
- ✅ Mobile browsers

## 🎯 Best Practices

### Test Organization
- **Descriptive Names**: Clear test and screenshot naming
- **Logical Grouping**: Tests organized by functionality
- **Reusable Utilities**: Common functions in utils/
- **Test Data Fixtures**: Centralized test data management

### Screenshot Strategy
- **Consistent Timing**: Wait for network idle before screenshots
- **Animation Control**: Disable animations for consistent results
- **Full Coverage**: Both component and page-level captures
- **Error States**: Capture error conditions and edge cases

### Performance Testing
- **Realistic Conditions**: Network throttling for mobile
- **Memory Monitoring**: JavaScript heap usage tracking
- **Response Time Validation**: API and page load benchmarks
- **Resource Optimization**: Bundle size and loading efficiency

## 🚀 Continuous Integration

### GitHub Actions Integration
```yaml
- name: Run Playwright Tests
  run: |
    cd tests/playwright
    ./run-tests.sh
- name: Upload Screenshots
  uses: actions/upload-artifact@v3
  with:
    name: playwright-screenshots
    path: tests/playwright/test-results/
```

### Docker Integration
```dockerfile
FROM mcr.microsoft.com/playwright:focal
COPY tests/playwright/ /app/tests/
WORKDIR /app/tests
RUN npm install
CMD ["npx", "playwright", "test"]
```

## 📞 Support

For issues with the testing suite:

1. **Check Services**: Ensure backend (8000) and frontend (3000) are running
2. **Browser Issues**: Run `npx playwright install --with-deps`
3. **Permission Errors**: Check file permissions on test scripts
4. **Screenshot Failures**: Verify display resolution and graphics drivers
5. **Network Issues**: Check firewall and proxy settings

## 🎉 Success Indicators

When tests complete successfully, you should see:

- ✅ All test suites passing
- 📸 Screenshots captured for each test scenario  
- 📊 Performance metrics within acceptable ranges
- 📋 HTML report with visual evidence
- 🎯 100% visual coverage of application features

The comprehensive test suite ensures the eBay Manager application is fully functional, visually consistent, and performs well across all supported browsers and devices.