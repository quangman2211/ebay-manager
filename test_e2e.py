#!/usr/bin/env python3
"""
End-to-end testing script for the complete eBay Manager application
"""
import subprocess
import time
import requests
import json
import os
import signal

class E2ETestRunner:
    def __init__(self):
        self.backend_process = None
        self.backend_url = "http://localhost:8000"
        self.test_results = []
    
    def start_backend(self):
        """Start the backend server"""
        print("🚀 Starting backend server...")
        
        # Change to backend directory and start server
        os.chdir('/home/quangman/EBAY/ebay-manager/backend')
        
        # Activate virtual environment and start server
        cmd = ['bash', '-c', 'source venv/bin/activate && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000']
        
        self.backend_process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait for server to start
        for i in range(30):  # Wait up to 30 seconds
            try:
                response = requests.get(f"{self.backend_url}/docs", timeout=2)
                if response.status_code == 200:
                    print("✅ Backend server started successfully")
                    return True
            except:
                pass
            time.sleep(1)
        
        print("❌ Backend server failed to start")
        return False
    
    def stop_backend(self):
        """Stop the backend server"""
        if self.backend_process:
            self.backend_process.terminate()
            self.backend_process.wait(timeout=10)
            print("🛑 Backend server stopped")
    
    def test_api_endpoints(self):
        """Test critical API endpoints"""
        print("\n🧪 Testing API endpoints...")
        
        try:
            # Test 1: API Documentation
            response = requests.get(f"{self.backend_url}/docs", timeout=10)
            assert response.status_code == 200, f"API docs failed: {response.status_code}"
            print("✅ API documentation accessible")
            
            # Test 2: Authentication endpoint
            auth_data = {"username": "admin", "password": "admin123"}
            response = requests.post(f"{self.backend_url}/api/v1/login", data=auth_data, timeout=10)
            assert response.status_code == 200, f"Login failed: {response.status_code}"
            
            token = response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            print("✅ Authentication working")
            
            # Test 3: Protected endpoint
            response = requests.get(f"{self.backend_url}/api/v1/accounts", headers=headers, timeout=10)
            assert response.status_code == 200, f"Protected endpoint failed: {response.status_code}"
            print("✅ Protected endpoints accessible")
            
            # Test 4: User info endpoint
            response = requests.get(f"{self.backend_url}/api/v1/me", headers=headers, timeout=10)
            assert response.status_code == 200, f"User info failed: {response.status_code}"
            user_data = response.json()
            assert user_data["username"] == "admin", f"Expected admin user, got {user_data['username']}"
            print("✅ User information correct")
            
            self.test_results.append("✅ API endpoints: All tests passed")
            return True
            
        except Exception as e:
            print(f"❌ API endpoint test failed: {e}")
            self.test_results.append(f"❌ API endpoints: {e}")
            return False
    
    def test_csv_upload(self):
        """Test CSV upload functionality"""
        print("\n🧪 Testing CSV upload functionality...")
        
        try:
            # Login first
            auth_data = {"username": "admin", "password": "admin123"}
            response = requests.post(f"{self.backend_url}/api/v1/login", data=auth_data, timeout=10)
            token = response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            
            # Create an account first
            account_data = {
                "ebay_username": "test_account",
                "name": "Test Account",
                "is_active": True
            }
            response = requests.post(f"{self.backend_url}/api/v1/accounts", json=account_data, headers=headers, timeout=10)
            assert response.status_code == 200, f"Account creation failed: {response.status_code}"
            account_id = response.json()["id"]
            print("✅ Test account created")
            
            # Test order CSV upload
            order_csv_path = "/home/quangman/EBAY/ebay-manager/Docs/DATA/ebay-order.csv"
            if os.path.exists(order_csv_path):
                with open(order_csv_path, 'rb') as f:
                    files = {'file': ('ebay-order.csv', f, 'text/csv')}
                    data = {'account_id': account_id, 'data_type': 'order'}
                    
                    response = requests.post(f"{self.backend_url}/api/v1/csv/upload", 
                                           files=files, data=data, headers=headers, timeout=30)
                    assert response.status_code == 200, f"Order upload failed: {response.status_code}"
                    
                    result = response.json()
                    assert result['inserted_count'] == 4, f"Expected 4 orders, got {result['inserted_count']}"
                    print(f"✅ Order CSV uploaded: {result['inserted_count']} records")
            
            # Test listing CSV upload
            listing_csv_path = "/home/quangman/EBAY/ebay-manager/Docs/DATA/ebay-listing.csv"
            if os.path.exists(listing_csv_path):
                with open(listing_csv_path, 'rb') as f:
                    files = {'file': ('ebay-listing.csv', f, 'text/csv')}
                    data = {'account_id': account_id, 'data_type': 'listing'}
                    
                    response = requests.post(f"{self.backend_url}/api/v1/csv/upload", 
                                           files=files, data=data, headers=headers, timeout=30)
                    assert response.status_code == 200, f"Listing upload failed: {response.status_code}"
                    
                    result = response.json()
                    assert result['inserted_count'] == 115, f"Expected 115 listings, got {result['inserted_count']}"
                    print(f"✅ Listing CSV uploaded: {result['inserted_count']} records")
            
            self.test_results.append("✅ CSV upload: All tests passed")
            return True
            
        except Exception as e:
            print(f"❌ CSV upload test failed: {e}")
            self.test_results.append(f"❌ CSV upload: {e}")
            return False
    
    def test_order_management(self):
        """Test order management workflow"""
        print("\n🧪 Testing order management...")
        
        try:
            # Login first
            auth_data = {"username": "admin", "password": "admin123"}
            response = requests.post(f"{self.backend_url}/api/v1/login", data=auth_data, timeout=10)
            token = response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            
            # Get accounts
            response = requests.get(f"{self.backend_url}/api/v1/accounts", headers=headers, timeout=10)
            accounts = response.json()
            assert len(accounts) > 0, "No accounts found"
            account_id = accounts[0]["id"]
            
            # Get orders
            response = requests.get(f"{self.backend_url}/api/v1/orders?account_id={account_id}", headers=headers, timeout=10)
            assert response.status_code == 200, f"Orders retrieval failed: {response.status_code}"
            orders = response.json()
            
            if orders:
                order_id = orders[0]["id"]
                print(f"✅ Retrieved {len(orders)} orders")
                
                # Test status update
                for status in ['processing', 'shipped', 'completed']:
                    response = requests.put(
                        f"{self.backend_url}/api/v1/orders/{order_id}/status",
                        json={"status": status},
                        headers=headers,
                        timeout=10
                    )
                    assert response.status_code == 200, f"Status update to {status} failed: {response.status_code}"
                    print(f"✅ Order status updated to {status}")
                
                # Test status filtering
                response = requests.get(f"{self.backend_url}/api/v1/orders?account_id={account_id}&status=completed", 
                                      headers=headers, timeout=10)
                completed_orders = response.json()
                assert len(completed_orders) > 0, "No completed orders found after update"
                print("✅ Order status filtering working")
            
            self.test_results.append("✅ Order management: All tests passed")
            return True
            
        except Exception as e:
            print(f"❌ Order management test failed: {e}")
            self.test_results.append(f"❌ Order management: {e}")
            return False
    
    def test_performance(self):
        """Test application performance"""
        print("\n🧪 Testing application performance...")
        
        try:
            # Test API response times
            start_time = time.time()
            response = requests.get(f"{self.backend_url}/docs", timeout=10)
            docs_time = time.time() - start_time
            assert docs_time < 2.0, f"API docs too slow: {docs_time:.2f}s"
            print(f"✅ API docs load time: {docs_time:.2f}s")
            
            # Test authentication response time
            auth_data = {"username": "admin", "password": "admin123"}
            start_time = time.time()
            response = requests.post(f"{self.backend_url}/api/v1/login", data=auth_data, timeout=10)
            auth_time = time.time() - start_time
            assert auth_time < 1.0, f"Authentication too slow: {auth_time:.2f}s"
            print(f"✅ Authentication time: {auth_time:.2f}s")
            
            self.test_results.append("✅ Performance: All tests passed")
            return True
            
        except Exception as e:
            print(f"❌ Performance test failed: {e}")
            self.test_results.append(f"❌ Performance: {e}")
            return False
    
    def run_all_tests(self):
        """Run all end-to-end tests"""
        print("🎯 Starting End-to-End Testing Suite...")
        print("="*60)
        
        try:
            # Start backend
            if not self.start_backend():
                return False
            
            # Run tests
            tests = [
                self.test_api_endpoints,
                self.test_csv_upload,
                self.test_order_management,
                self.test_performance
            ]
            
            all_passed = True
            for test in tests:
                try:
                    if not test():
                        all_passed = False
                except Exception as e:
                    print(f"❌ Test failed with exception: {e}")
                    all_passed = False
            
            # Print summary
            print("\n" + "="*60)
            print("📋 TEST SUMMARY")
            print("="*60)
            
            for result in self.test_results:
                print(result)
            
            if all_passed:
                print("\n🎉 ALL END-TO-END TESTS PASSED!")
                print("🚀 Application is ready for deployment!")
            else:
                print("\n❌ Some tests failed!")
                
            return all_passed
            
        finally:
            self.stop_backend()

if __name__ == "__main__":
    runner = E2ETestRunner()
    success = runner.run_all_tests()
    exit(0 if success else 1)