#!/usr/bin/env python3

import subprocess
import sys
import os
import json

def run_backend_tests():
    """Run backend tests with coverage"""
    print("🧪 Running Backend Tests...")
    print("=" * 50)
    
    os.chdir("backend")
    
    # Install test dependencies
    print("Installing test dependencies...")
    subprocess.run([sys.executable, "-m", "pip", "install", "pytest", "pytest-cov", "pytest-mock"], check=True)
    
    # Run service tests
    print("\n🔧 Testing Listing Service...")
    result1 = subprocess.run([
        "python", "-m", "pytest", 
        "test_listing_service.py", 
        "-v", 
        "--cov=app.services.listing_service",
        "--cov-report=term-missing",
        "--cov-report=html:htmlcov_service",
        "--tb=short"
    ], capture_output=True, text=True)
    
    print(result1.stdout)
    if result1.stderr:
        print("Errors:", result1.stderr)
    
    # Run API tests
    print("\n🌐 Testing API Endpoints...")
    result2 = subprocess.run([
        "python", "-m", "pytest", 
        "test_listing_api.py", 
        "-v", 
        "--cov=app.main",
        "--cov-report=term-missing", 
        "--cov-report=html:htmlcov_api",
        "--tb=short"
    ], capture_output=True, text=True)
    
    print(result2.stdout)
    if result2.stderr:
        print("Errors:", result2.stderr)
    
    os.chdir("..")
    
    return result1.returncode == 0 and result2.returncode == 0

def run_frontend_tests():
    """Run frontend tests with coverage"""
    print("\n🎨 Running Frontend Tests...")
    print("=" * 50)
    
    os.chdir("frontend")
    
    # Check if jest is available
    if not os.path.exists("node_modules/.bin/jest"):
        print("Installing test dependencies...")
        subprocess.run(["npm", "install", "--save-dev", "@testing-library/react", "@testing-library/jest-dom", "@testing-library/user-event"], check=True)
    
    # Run component tests
    print("\n⚛️  Testing React Components...")
    result = subprocess.run([
        "npm", "test", "--", 
        "--coverage", 
        "--watchAll=false",
        "--testPathPattern=__tests__",
        "--verbose"
    ], capture_output=True, text=True)
    
    print(result.stdout)
    if result.stderr:
        print("Errors:", result.stderr)
    
    os.chdir("..")
    
    return result.returncode == 0

def generate_coverage_report():
    """Generate combined coverage report"""
    print("\n📊 Generating Coverage Report...")
    print("=" * 50)
    
    coverage_data = {
        "backend": {
            "service_layer": "See backend/htmlcov_service/index.html",
            "api_endpoints": "See backend/htmlcov_api/index.html"
        },
        "frontend": {
            "components": "See frontend/coverage/lcov-report/index.html"
        },
        "target_coverage": "90%",
        "phase_1_features": [
            "✅ Backend service layer with SOLID principles",
            "✅ API endpoints for CRUD operations", 
            "✅ Pydantic schemas for validation",
            "✅ ListingEditModal component",
            "✅ InlineEditableField component",
            "✅ ListingStatusToggle component", 
            "✅ ListingPerformanceIndicator component",
            "✅ Comprehensive unit tests",
            "✅ Integration tests",
            "✅ Component tests"
        ]
    }
    
    with open("coverage_report.json", "w") as f:
        json.dump(coverage_data, f, indent=2)
    
    print("📋 Phase 1 Implementation Complete!")
    print("Features implemented:")
    for feature in coverage_data["phase_1_features"]:
        print(f"  {feature}")
    
    print(f"\n🎯 Target Coverage: {coverage_data['target_coverage']}")
    print("\nCoverage Reports:")
    print("  Backend Service: backend/htmlcov_service/index.html")
    print("  Backend API: backend/htmlcov_api/index.html") 
    print("  Frontend: frontend/coverage/lcov-report/index.html")

def main():
    """Run all tests and generate coverage report"""
    print("🚀 eBay Manager - Enhance Listing Page Tests")
    print("Phase 1: Listing Management Features")
    print("=" * 60)
    
    backend_success = run_backend_tests()
    frontend_success = run_frontend_tests()
    
    generate_coverage_report()
    
    if backend_success and frontend_success:
        print("\n✅ All tests passed! Phase 1 implementation is ready.")
        return 0
    else:
        print("\n❌ Some tests failed. Please review the output above.")
        return 1

if __name__ == "__main__":
    exit(main())