# Comprehensive GUI Testing for Merged Features

## Overview
This document outlines the comprehensive Playwright testing strategy for the newly merged enhanced upload functionality and account deletion system with data preservation.

## 🎯 Test Coverage

### Phase 1: Enhanced Bulk CSV Upload System

#### Test Suite 1.1: Bulk Upload Interface & Drag-and-Drop
- ✅ Verify drag-and-drop multiple CSV files functionality
- ✅ Test bulk upload table with file management (add/remove files)
- ✅ Validate data type selection per file (Order/Listing)
- ✅ Test account selection dropdown for each file
- ✅ Account mismatch warning dialog validation

#### Test Suite 1.2: CSV Processing & Progress Tracking
- ✅ Upload progress indicators for multiple files
- ✅ Real-time status updates (pending → uploading → completed/failed)
- ✅ Error handling and recovery UI testing
- ✅ CSV validation error display and user feedback

#### Test Suite 1.3: Smart Detection Features
- ✅ Automatic account suggestion based on detected usernames
- ✅ Account matching (exact vs partial matches)
- ✅ Auto-population of detected platform usernames

### Phase 2: Account Deletion with Data Preservation

#### Test Suite 2.1: Account Deletion Dialog
- ✅ Data impact preview display (orders, listings, permissions count)
- ✅ Radio button selection (Transfer vs Delete permanently)
- ✅ GUEST account transfer option validation
- ✅ Visual warning indicators and confirmation flow

#### Test Suite 2.2: Data Preservation Workflows
- ✅ Test transfer data to GUEST account scenario
- ✅ Validate permanent deletion with data removal
- ✅ Account status updates after deletion
- ✅ Data integrity verification post-deletion

### Phase 3: Integration & End-to-End Workflows

#### Test Suite 3.1: Complete User Journey
- ✅ Login → Account Management → Delete Account with data transfer
- ✅ Upload CSV → Account mismatch warning → Resolve and upload
- ✅ Bulk upload multiple files with different data types
- ✅ Account deletion impact on upload functionality

#### Test Suite 3.2: GUEST Account System Verification
- ✅ GUEST account visibility in account management
- ✅ GUEST account protection (non-deletable)
- ✅ Health check endpoint validation
- ✅ Data transfer verification

## 🛠️ Test Execution

### Quick Start
```bash
# Navigate to test directory
cd tests/playwright

# Run all merged features tests (headless)
node run-merged-features-gui.js

# Run tests with GUI (headed mode)
HEADLESS=false node run-merged-features-gui.js
```

### Individual Test Suites
```bash
# Run specific test groups
npx playwright test tests/merged-features.spec.ts -g "Bulk Upload"
npx playwright test tests/merged-features.spec.ts -g "Account Deletion"
npx playwright test tests/merged-features.spec.ts -g "Integration"

# Run with specific browsers
npx playwright test tests/merged-features.spec.ts --project=chromium
npx playwright test tests/merged-features.spec.ts --project=firefox
```

### Debug Mode
```bash
# Run in debug mode with Playwright Inspector
npx playwright test tests/merged-features.spec.ts --debug

# Run specific test with headed browser and slow motion
npx playwright test tests/merged-features.spec.ts -g "Account Deletion Dialog" --headed --slowMo=2000
```

## 📊 Test Reports & Artifacts

### Generated Reports
- **HTML Report**: `playwright-report/index.html`
- **JSON Report**: `test-results.json`
- **Screenshots**: `test-results/*.png`
- **Videos**: `test-results/*.webm` (on failures)

### Screenshot Naming Convention
- `bulk-upload-*`: Bulk upload functionality tests
- `account-deletion-*`: Account deletion dialog tests
- `e2e-*`: End-to-end workflow tests
- `error-*`: Error handling scenarios
- `guest-account-*`: GUEST account system tests

## 🎮 Interactive Testing with MCP Playwright

### Using MCP Playwright Browser Automation
```bash
# Start backend server
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000

# Start frontend server
cd frontend
npm start

# Run MCP Playwright tests
# The tests will automatically use MCP browser automation
```

### MCP Playwright Features Used
- **Browser Navigation**: Automated page navigation and form interactions
- **File Upload**: Drag-and-drop and file selection automation
- **Dialog Handling**: Modal dialog interactions and confirmations
- **Element Interactions**: Click, type, select operations
- **Screenshot Capture**: Visual documentation of test states
- **Wait Strategies**: Smart waiting for dynamic content

## 🔍 Test Data Files

### CSV Test Files
- `test-sample.csv`: Basic order data (4 records)
- `fixtures/test-orders-large.csv`: Larger order dataset (10 records)
- `fixtures/test-listings.csv`: Listing data for testing

### Test Scenarios Data
- Valid CSV formats with proper headers
- Invalid file types for error testing
- Files with detected usernames for account matching
- Edge cases (empty files, malformed data)

## 🎯 Test Validation Points

### UI Element Validation
- ✅ Dropzone visibility and functionality
- ✅ Table display with correct columns
- ✅ Progress indicators and status updates
- ✅ Error messages and alerts
- ✅ Dialog components and interactions

### API Integration Validation
- ✅ Upload endpoint responses
- ✅ Account suggestion API calls
- ✅ Deletion impact API data
- ✅ GUEST account health checks
- ✅ Progress tracking endpoints

### Data Flow Validation
- ✅ File processing workflows
- ✅ Account data preservation
- ✅ GUEST account data transfer
- ✅ UI state management
- ✅ Error recovery processes

## 🌐 Browser Compatibility

### Tested Browsers
- **Chrome/Chromium**: Primary testing browser
- **Firefox**: Cross-browser validation
- **Safari/WebKit**: Mobile and desktop compatibility
- **Mobile Chrome**: Mobile responsiveness
- **Mobile Safari**: iOS compatibility

### Responsive Testing
- Desktop viewports (1920x1080, 1366x768)
- Tablet viewports (iPad, Android tablets)
- Mobile viewports (iPhone, Android phones)

## 🚨 Error Scenarios Covered

### Upload Error Handling
- Invalid file types (.txt, .json instead of .csv)
- Missing account selection
- Network failures during upload
- Server-side validation errors
- Large file timeout scenarios

### Account Deletion Error Handling
- Deletion of non-existent accounts
- GUEST account deletion attempts (should be blocked)
- Network failures during deletion
- Data transfer validation failures

## 📈 Performance Testing

### Metrics Collected
- Upload processing time
- UI responsiveness during operations
- Memory usage during bulk operations
- Network request efficiency
- Error recovery time

### Benchmarks
- Single file upload: < 5 seconds
- Bulk upload (10 files): < 30 seconds
- Account deletion dialog: < 2 seconds to load
- Data impact calculation: < 3 seconds

## 🔧 Troubleshooting

### Common Issues
1. **Test Timeout**: Increase timeout in playwright.config.ts
2. **File Not Found**: Check test data file paths
3. **Authentication**: Verify test credentials in fixtures
4. **Server Not Running**: Ensure backend/frontend are started

### Debug Commands
```bash
# Check if servers are running
curl http://localhost:8000/api/v1/health/guest-account
curl http://localhost:3000

# View test logs
npx playwright show-report

# Open trace viewer
npx playwright show-trace test-results/trace.zip
```

## 🎉 Expected Results

After successful test execution, you should see:
- ✅ All test suites passing with green checkmarks
- 📸 Screenshot documentation of all UI states
- 📊 Comprehensive HTML report with test metrics
- 🎬 Video recordings of any failed tests for debugging
- 📋 JSON report for CI/CD integration

## 🚀 Next Steps

1. **Run the comprehensive test suite**
2. **Review generated reports and screenshots**
3. **Address any failing test scenarios**
4. **Integrate with CI/CD pipeline**
5. **Schedule regular regression testing**