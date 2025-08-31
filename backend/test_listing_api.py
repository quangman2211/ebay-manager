import pytest
import json
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import get_db, Base
from app.models import User, Account, CSVData
from app.auth import create_access_token


# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_listings.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(scope="module")
def setup_database():
    """Setup test database with sample data"""
    Base.metadata.create_all(bind=engine)
    
    db = TestingSessionLocal()
    
    # Create test user
    test_user = User(
        username="testuser",
        email="test@example.com",
        password_hash="hashed_password",
        role="staff"
    )
    db.add(test_user)
    db.commit()
    db.refresh(test_user)
    
    # Create test account
    test_account = Account(
        user_id=test_user.id,
        ebay_username="test_ebay",
        name="Test Account"
    )
    db.add(test_account)
    db.commit()
    db.refresh(test_account)
    
    # Create test listing
    test_listing = CSVData(
        account_id=test_account.id,
        data_type="listing",
        item_id="123456789",
        csv_row={
            "Title": "Test Product",
            "Current price": "19.99",
            "Start price": "19.99",
            "Available quantity": "10",
            "Sold quantity": "5",
            "Watchers": "8",
            "Status": "active",
            "Format": "FIXED_PRICE"
        }
    )
    db.add(test_listing)
    db.commit()
    db.refresh(test_listing)
    
    db.close()
    
    yield {
        "user_id": test_user.id,
        "account_id": test_account.id,
        "listing_id": test_listing.id
    }
    
    # Cleanup
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def auth_headers(setup_database):
    """Create authentication headers for test requests"""
    token = create_access_token(data={"sub": "testuser"})
    return {"Authorization": f"Bearer {token}"}


class TestListingAPIEndpoints:
    """Test all listing API endpoints"""
    
    def test_get_listing_by_id_success(self, setup_database, auth_headers):
        """Test successful retrieval of listing by ID"""
        listing_id = setup_database["listing_id"]
        
        response = client.get(f"/api/v1/listings/{listing_id}", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == listing_id
        assert data["item_id"] == "123456789"
        assert data["csv_row"]["Title"] == "Test Product"
    
    def test_get_listing_by_id_not_found(self, auth_headers):
        """Test listing not found scenario"""
        response = client.get("/api/v1/listings/99999", headers=auth_headers)
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_get_listing_by_id_unauthorized(self, setup_database):
        """Test unauthorized access"""
        listing_id = setup_database["listing_id"]
        
        response = client.get(f"/api/v1/listings/{listing_id}")
        
        assert response.status_code == 401
    
    def test_update_listing_field_price(self, setup_database, auth_headers):
        """Test updating listing price field"""
        listing_id = setup_database["listing_id"]
        
        payload = {
            "field": "price",
            "value": "29.99"
        }
        
        response = client.put(f"/api/v1/listings/{listing_id}/field", json=payload, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "updated successfully" in data["message"]
        assert data["listing_id"] == listing_id
    
    def test_update_listing_field_quantity(self, setup_database, auth_headers):
        """Test updating listing quantity field"""
        listing_id = setup_database["listing_id"]
        
        payload = {
            "field": "quantity",
            "value": "15"
        }
        
        response = client.put(f"/api/v1/listings/{listing_id}/field", json=payload, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "updated successfully" in data["message"]
    
    def test_update_listing_field_invalid_price(self, setup_database, auth_headers):
        """Test updating with invalid price"""
        listing_id = setup_database["listing_id"]
        
        payload = {
            "field": "price",
            "value": "invalid_price"
        }
        
        response = client.put(f"/api/v1/listings/{listing_id}/field", json=payload, headers=auth_headers)
        
        assert response.status_code == 400
        assert "Invalid price" in response.json()["detail"]
    
    def test_update_listing_field_invalid_quantity(self, setup_database, auth_headers):
        """Test updating with invalid quantity"""
        listing_id = setup_database["listing_id"]
        
        payload = {
            "field": "quantity",
            "value": "-1"
        }
        
        response = client.put(f"/api/v1/listings/{listing_id}/field", json=payload, headers=auth_headers)
        
        assert response.status_code == 400
        assert "Invalid quantity" in response.json()["detail"]
    
    def test_update_listing_bulk(self, setup_database, auth_headers):
        """Test bulk update of multiple fields"""
        listing_id = setup_database["listing_id"]
        
        payload = {
            "updates": {
                "price": "39.99",
                "quantity": "20",
                "title": "Updated Test Product"
            }
        }
        
        response = client.put(f"/api/v1/listings/{listing_id}/bulk", json=payload, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "updated successfully" in data["message"]
    
    def test_update_listing_bulk_invalid_data(self, setup_database, auth_headers):
        """Test bulk update with invalid data"""
        listing_id = setup_database["listing_id"]
        
        payload = {
            "updates": {
                "price": "invalid",
                "quantity": "-5"
            }
        }
        
        response = client.put(f"/api/v1/listings/{listing_id}/bulk", json=payload, headers=auth_headers)
        
        assert response.status_code == 400
        assert "Invalid" in response.json()["detail"]
    
    def test_update_listing_comprehensive(self, setup_database, auth_headers):
        """Test comprehensive listing update"""
        listing_id = setup_database["listing_id"]
        
        payload = {
            "title": "Comprehensive Update Test",
            "price": "49.99",
            "quantity": "25",
            "status": "active"
        }
        
        response = client.put(f"/api/v1/listings/{listing_id}", json=payload, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "updated successfully" in data["message"]
    
    def test_update_listing_no_fields(self, setup_database, auth_headers):
        """Test update with no fields provided"""
        listing_id = setup_database["listing_id"]
        
        payload = {}
        
        response = client.put(f"/api/v1/listings/{listing_id}", json=payload, headers=auth_headers)
        
        assert response.status_code == 400
        assert "No fields to update" in response.json()["detail"]
    
    def test_get_listing_performance_metrics(self, setup_database, auth_headers):
        """Test getting performance metrics for a listing"""
        listing_id = setup_database["listing_id"]
        
        response = client.get(f"/api/v1/listings/{listing_id}/metrics", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        required_fields = [
            "sell_through_rate",
            "watchers_count", 
            "stock_status",
            "days_listed",
            "price_competitiveness"
        ]
        
        for field in required_fields:
            assert field in data
        
        assert data["watchers_count"] == 8
        assert data["sell_through_rate"] >= 0
        assert data["stock_status"] in ["in_stock", "low_stock", "out_of_stock"]
        assert data["price_competitiveness"] in ["competitive", "attractive", "moderate", "needs_review"]


class TestListingAPIValidation:
    """Test API validation and error handling"""
    
    def test_invalid_listing_id_type(self, auth_headers):
        """Test with invalid listing ID type"""
        response = client.get("/api/v1/listings/invalid_id", headers=auth_headers)
        
        assert response.status_code == 422  # Validation error
    
    def test_missing_required_fields(self, setup_database, auth_headers):
        """Test missing required fields in request"""
        listing_id = setup_database["listing_id"]
        
        # Missing 'field' in field update
        payload = {"value": "test"}
        response = client.put(f"/api/v1/listings/{listing_id}/field", json=payload, headers=auth_headers)
        
        assert response.status_code == 422
    
    def test_invalid_json_payload(self, setup_database, auth_headers):
        """Test with invalid JSON payload"""
        listing_id = setup_database["listing_id"]
        
        response = client.put(
            f"/api/v1/listings/{listing_id}/field",
            data="invalid json",
            headers={**auth_headers, "Content-Type": "application/json"}
        )
        
        assert response.status_code == 422


class TestListingAPIPermissions:
    """Test permission and access control"""
    
    @pytest.fixture
    def other_user_headers(self, setup_database):
        """Create headers for a different user"""
        db = TestingSessionLocal()
        
        # Create another user
        other_user = User(
            username="otheruser",
            email="other@example.com", 
            password_hash="hashed_password",
            role="staff"
        )
        db.add(other_user)
        db.commit()
        
        # Create account for other user
        other_account = Account(
            user_id=other_user.id,
            ebay_username="other_ebay",
            name="Other Account"
        )
        db.add(other_account)
        db.commit()
        
        db.close()
        
        token = create_access_token(data={"sub": "otheruser"})
        return {"Authorization": f"Bearer {token}"}
    
    def test_access_denied_to_other_user_listing(self, setup_database, other_user_headers):
        """Test that users cannot access listings from accounts they don't own"""
        listing_id = setup_database["listing_id"]
        
        response = client.get(f"/api/v1/listings/{listing_id}", headers=other_user_headers)
        
        assert response.status_code == 403
        assert "Access denied" in response.json()["detail"]


class TestListingAPIPerformance:
    """Test API performance and edge cases"""
    
    def test_concurrent_updates(self, setup_database, auth_headers):
        """Test handling of concurrent updates"""
        listing_id = setup_database["listing_id"]
        
        # Simulate concurrent price updates
        payloads = [
            {"field": "price", "value": "25.99"},
            {"field": "price", "value": "27.99"},
            {"field": "price", "value": "23.99"}
        ]
        
        responses = []
        for payload in payloads:
            response = client.put(f"/api/v1/listings/{listing_id}/field", json=payload, headers=auth_headers)
            responses.append(response)
        
        # All requests should succeed (last one wins)
        for response in responses:
            assert response.status_code == 200
    
    def test_large_bulk_update(self, setup_database, auth_headers):
        """Test bulk update with many fields"""
        listing_id = setup_database["listing_id"]
        
        payload = {
            "updates": {
                "title": "Very Long Title " * 10,  # Long title
                "price": "99.99",
                "quantity": "100", 
                "status": "active"
            }
        }
        
        response = client.put(f"/api/v1/listings/{listing_id}/bulk", json=payload, headers=auth_headers)
        
        # Should handle large updates gracefully
        assert response.status_code in [200, 400]  # Either success or validation error


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=app.main", "--cov-report=term-missing"])