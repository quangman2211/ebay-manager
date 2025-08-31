#!/bin/bash

# eBay Manager Playwright Test Runner
# Comprehensive testing script with visual screenshots and performance metrics

set -e

echo "🎭 eBay Manager - Playwright Testing Suite"
echo "==========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Create test results directory
mkdir -p test-results
mkdir -p playwright-report

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if backend and frontend are running
check_services() {
    print_status "Checking if services are running..."
    
    # Check backend
    if curl -s http://localhost:8000/docs > /dev/null 2>&1; then
        print_success "Backend is running on port 8000"
    else
        print_warning "Backend not detected on port 8000. Starting services..."
        cd ../../
        ./start-app.sh &
        SERVICES_PID=$!
        sleep 10
        
        # Check again
        if curl -s http://localhost:8000/docs > /dev/null 2>&1; then
            print_success "Backend started successfully"
        else
            print_error "Failed to start backend"
            exit 1
        fi
        
        cd tests/playwright
    fi
    
    # Check frontend
    if curl -s http://localhost:3000 > /dev/null 2>&1; then
        print_success "Frontend is running on port 3000"
    else
        print_error "Frontend not detected on port 3000"
        exit 1
    fi
}

# Install dependencies if needed
install_dependencies() {
    if [ ! -d "node_modules" ]; then
        print_status "Installing Playwright dependencies..."
        npm install
    fi
    
    # Check if browsers are installed
    if ! npx playwright list-browsers > /dev/null 2>&1; then
        print_status "Installing Playwright browsers..."
        npx playwright install --with-deps chromium firefox webkit
    fi
}

# Run specific test suite
run_test_suite() {
    local suite=$1
    local description=$2
    
    print_status "Running $description..."
    echo "----------------------------------------"
    
    if npx playwright test --project=chromium tests/$suite.spec.ts --reporter=list; then
        print_success "$description completed successfully"
        return 0
    else
        print_error "$description failed"
        return 1
    fi
    
    echo ""
}

# Main test execution
main() {
    local failed_tests=0
    local total_tests=0
    
    print_status "Starting comprehensive Playwright testing..."
    echo ""
    
    # Pre-flight checks
    install_dependencies
    check_services
    
    # Clear previous results
    rm -rf test-results/* 2>/dev/null || true
    rm -rf playwright-report/* 2>/dev/null || true
    
    echo ""
    print_status "🚀 Beginning test execution..."
    echo "============================================="
    
    # Test Suite 1: Backend API Testing
    total_tests=$((total_tests + 1))
    if run_test_suite "backend-api" "Backend API Visual Testing"; then
        print_success "✅ Backend API tests passed"
    else
        failed_tests=$((failed_tests + 1))
        print_error "❌ Backend API tests failed"
    fi
    
    # Test Suite 2: Frontend UI Testing
    total_tests=$((total_tests + 1))
    if run_test_suite "frontend-ui" "Frontend UI Component Testing"; then
        print_success "✅ Frontend UI tests passed"
    else
        failed_tests=$((failed_tests + 1))
        print_error "❌ Frontend UI tests failed"
    fi
    
    # Test Suite 3: End-to-End Workflow Testing
    total_tests=$((total_tests + 1))
    if run_test_suite "e2e-workflows" "End-to-End Workflow Testing"; then
        print_success "✅ E2E Workflow tests passed"
    else
        failed_tests=$((failed_tests + 1))
        print_error "❌ E2E Workflow tests failed"
    fi
    
    # Test Suite 4: Visual Regression and Performance
    total_tests=$((total_tests + 1))
    if run_test_suite "visual-regression" "Visual Regression & Performance Testing"; then
        print_success "✅ Visual & Performance tests passed"
    else
        failed_tests=$((failed_tests + 1))
        print_error "❌ Visual & Performance tests failed"
    fi
    
    # Generate comprehensive report
    print_status "Generating test reports..."
    npx playwright show-report --host 0.0.0.0 > /dev/null 2>&1 &
    REPORT_PID=$!
    sleep 2
    
    # Count screenshots generated
    screenshot_count=$(find test-results -name "*.png" | wc -l)
    
    echo ""
    print_status "📊 Test Execution Summary"
    echo "=========================================="
    echo "Total Test Suites: $total_tests"
    echo "Passed: $((total_tests - failed_tests))"
    echo "Failed: $failed_tests"
    echo "Screenshots Captured: $screenshot_count"
    echo ""
    
    if [ $failed_tests -eq 0 ]; then
        print_success "🎉 ALL TESTS PASSED!"
        print_success "📸 Screenshots saved to: test-results/"
        print_success "📋 Full report available at: http://localhost:9323"
        echo ""
        print_status "Key Visual Evidence:"
        echo "  • API Documentation: test-results/api-docs-*.png"
        echo "  • Login Flow: test-results/e2e-*-login-*.png"
        echo "  • Dashboard: test-results/visual-baseline-dashboard-*.png"
        echo "  • Order Management: test-results/e2e-*-orders-*.png"
        echo "  • CSV Upload: test-results/e2e-csv-workflow-*.png"
        echo "  • Responsive Design: test-results/e2e-responsive-*.png"
        return 0
    else
        print_error "❌ $failed_tests test suite(s) failed"
        print_warning "Check individual test results and screenshots for details"
        return 1
    fi
}

# Cleanup function
cleanup() {
    if [ ! -z "$SERVICES_PID" ]; then
        print_status "Cleaning up services..."
        kill $SERVICES_PID 2>/dev/null || true
    fi
    
    if [ ! -z "$REPORT_PID" ]; then
        kill $REPORT_PID 2>/dev/null || true
    fi
}

# Set trap for cleanup
trap cleanup EXIT

# Execute main function
main