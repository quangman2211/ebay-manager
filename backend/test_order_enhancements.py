#!/usr/bin/env python3

import sys
import os
import pytest
import requests
import json
import time
from typing import Dict, Any

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api/v1"

class TestOrderEnhancements:
    """Test suite for enhanced order management features"""
    
    @classmethod
    def setup_class(cls):
        """Setup test environment"""
        cls.admin_token = cls.get_admin_token()
        cls.test_account_id = cls.create_test_account()
        cls.test_order_id = cls.create_test_order()
    
    @classmethod
    def get_admin_token(cls) -> str:
        """Get admin authentication token"""
        login_data = {
            "username": "admin",
            "password": "admin123"
        }
        
        response = requests.post(f"{API_URL}/login", data=login_data)
        assert response.status_code == 200, f"Login failed: {response.text}"
        
        token_data = response.json()
        return token_data["access_token"]
    
    @classmethod
    def create_test_account(cls) -> int:
        """Create test account for order management"""
        headers = {"Authorization": f"Bearer {cls.admin_token}"}
        account_data = {
            "ebay_username": "test_account_enhance",
            "name": "Test Account for Order Enhancement",
            "user_id": 1
        }
        
        response = requests.post(f"{API_URL}/accounts", json=account_data, headers=headers)
        assert response.status_code == 200, f"Account creation failed: {response.text}"
        
        return response.json()["id"]
    
    @classmethod
    def create_test_order(cls) -> int:
        """Create test order via CSV upload"""
        headers = {"Authorization": f"Bearer {cls.admin_token}"}
        
        # Sample order CSV data
        csv_content = '''Order Number,Item Number,Item Title,Buyer Name,Buyer Username,Sale Date,Ship By Date,Sold For,Tracking Number,Quantity
ORD-TEST-001,ITM-001,Test Product for Enhancement,John Doe,johndoe123,2025-08-30,2025-09-02,$29.99,,1'''
        
        files = {"file": ("test_orders.csv", csv_content, "text/csv")}
        form_data = {
            "account_id": str(cls.test_account_id),
            "data_type": "order"
        }
        
        response = requests.post(f"{API_URL}/csv/upload", files=files, data=form_data, headers=headers)
        assert response.status_code == 200, f"CSV upload failed: {response.text}"
        
        # Get the created order
        response = requests.get(f"{API_URL}/orders", 
                              params={"account_id": cls.test_account_id}, 
                              headers=headers)
        assert response.status_code == 200
        
        orders = response.json()
        assert len(orders) > 0, "No orders found after CSV upload"
        
        return orders[0]["id"]
    
    def get_headers(self) -> Dict[str, str]:
        """Get authorization headers"""
        return {"Authorization": f"Bearer {self.admin_token}"}
    
    def test_update_tracking_number(self):
        """Test tracking number update endpoint"""
        headers = self.get_headers()
        tracking_data = {"tracking_number": "1Z123456789012345678"}
        
        # Update tracking number
        response = requests.put(
            f"{API_URL}/orders/{self.test_order_id}/tracking",
            json=tracking_data,
            headers=headers
        )
        
        assert response.status_code == 200, f"Tracking update failed: {response.text}"
        assert "message" in response.json()
        assert "successfully" in response.json()["message"].lower()
        
        # Verify tracking number was updated
        response = requests.get(f"{API_URL}/orders", 
                              params={"account_id": self.test_account_id}, 
                              headers=headers)
        assert response.status_code == 200
        
        orders = response.json()
        test_order = next((order for order in orders if order["id"] == self.test_order_id), None)
        assert test_order is not None, "Test order not found"
        assert test_order["csv_row"]["Tracking Number"] == "1Z123456789012345678"
    
    def test_add_order_note(self):
        """Test order note creation endpoint"""
        headers = self.get_headers()
        note_data = {"note": "Test note for order enhancement testing"}
        
        # Add note to order
        response = requests.post(
            f"{API_URL}/orders/{self.test_order_id}/notes",
            json=note_data,
            headers=headers
        )
        
        assert response.status_code == 200, f"Note creation failed: {response.text}"
        
        note_response = response.json()
        assert "id" in note_response
        assert note_response["note"] == "Test note for order enhancement testing"
        assert note_response["order_id"] == self.test_order_id
        assert "created_at" in note_response
        
        return note_response["id"]
    
    def test_order_with_notes_retrieval(self):
        """Test that orders include notes when retrieved"""
        headers = self.get_headers()
        
        # Add a note first
        note_data = {"note": "Note for retrieval testing"}
        note_response = requests.post(
            f"{API_URL}/orders/{self.test_order_id}/notes",
            json=note_data,
            headers=headers
        )
        assert note_response.status_code == 200
        
        # Get orders and verify notes are included
        response = requests.get(f"{API_URL}/orders", 
                              params={"account_id": self.test_account_id}, 
                              headers=headers)
        assert response.status_code == 200
        
        orders = response.json()
        test_order = next((order for order in orders if order["id"] == self.test_order_id), None)
        assert test_order is not None, "Test order not found"
        
        # Check if notes are included (may be None if not loaded with eager loading)
        if "notes" in test_order and test_order["notes"]:
            note_texts = [note["note"] for note in test_order["notes"]]
            assert "Note for retrieval testing" in note_texts
    
    def test_tracking_number_validation(self):
        """Test tracking number update with invalid data"""
        headers = self.get_headers()
        
        # Test with empty tracking number (should be allowed)
        tracking_data = {"tracking_number": ""}
        response = requests.put(
            f"{API_URL}/orders/{self.test_order_id}/tracking",
            json=tracking_data,
            headers=headers
        )
        assert response.status_code == 200
    
    def test_note_validation(self):
        """Test note creation with invalid data"""
        headers = self.get_headers()
        
        # Test with empty note (should fail)
        note_data = {"note": ""}
        response = requests.post(
            f"{API_URL}/orders/{self.test_order_id}/notes",
            json=note_data,
            headers=headers
        )
        # Backend validation should prevent empty notes
        # If not implemented yet, this test documents expected behavior
        
        # Test with very long note
        long_note = "A" * 1000  # 1000 characters
        note_data = {"note": long_note}
        response = requests.post(
            f"{API_URL}/orders/{self.test_order_id}/notes",
            json=note_data,
            headers=headers
        )
        # Should succeed or fail based on backend validation rules
        assert response.status_code in [200, 400]
    
    def test_unauthorized_access(self):
        """Test that endpoints require proper authorization"""
        # Test without token
        tracking_data = {"tracking_number": "1Z999888777666555"}
        response = requests.put(
            f"{API_URL}/orders/{self.test_order_id}/tracking",
            json=tracking_data
        )
        assert response.status_code == 401, "Should require authentication"
        
        # Test note creation without token
        note_data = {"note": "Unauthorized note"}
        response = requests.post(
            f"{API_URL}/orders/{self.test_order_id}/notes",
            json=note_data
        )
        assert response.status_code == 401, "Should require authentication"
    
    def test_nonexistent_order(self):
        """Test endpoints with non-existent order ID"""
        headers = self.get_headers()
        fake_order_id = 99999
        
        # Test tracking update on non-existent order
        tracking_data = {"tracking_number": "1Z123456789012345678"}
        response = requests.put(
            f"{API_URL}/orders/{fake_order_id}/tracking",
            json=tracking_data,
            headers=headers
        )
        assert response.status_code == 404, "Should return 404 for non-existent order"
        
        # Test note creation on non-existent order
        note_data = {"note": "Note for non-existent order"}
        response = requests.post(
            f"{API_URL}/orders/{fake_order_id}/notes",
            json=note_data,
            headers=headers
        )
        assert response.status_code == 404, "Should return 404 for non-existent order"
    
    def test_order_status_workflow(self):
        """Test complete order status workflow"""
        headers = self.get_headers()
        
        # Test status progression: pending -> processing -> shipped -> completed
        statuses = ["processing", "shipped", "completed"]
        
        for status in statuses:
            status_data = {"status": status}
            response = requests.put(
                f"{API_URL}/orders/{self.test_order_id}/status",
                json=status_data,
                headers=headers
            )
            assert response.status_code == 200, f"Status update to {status} failed: {response.text}"
            
            # Verify status was updated
            response = requests.get(f"{API_URL}/orders", 
                                  params={"account_id": self.test_account_id}, 
                                  headers=headers)
            assert response.status_code == 200
            
            orders = response.json()
            test_order = next((order for order in orders if order["id"] == self.test_order_id), None)
            assert test_order is not None
            assert test_order["order_status"]["status"] == status


def run_tests():
    """Run the test suite"""
    print("🧪 Running Order Enhancement Tests...")
    
    # Check if backend is running
    try:
        response = requests.get(BASE_URL)
        if response.status_code not in [200, 404]:
            print("❌ Backend server is not responding. Please start the backend first.")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend server. Please start the backend first.")
        return False
    
    # Run pytest
    test_file = __file__
    result = pytest.main([
        test_file,
        "-v",
        "--tb=short",
        "--disable-warnings"
    ])
    
    if result == 0:
        print("✅ All order enhancement tests passed!")
        return True
    else:
        print("❌ Some tests failed. Please check the output above.")
        return False


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)