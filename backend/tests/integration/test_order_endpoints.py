"""
Integration tests for Order API Endpoints
Following SOLID principles for comprehensive API testing
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from decimal import Decimal

from app.models.order import Order, OrderItem, OrderStatus, PaymentStatus, ShippingStatus
from app.models.user import User
from app.models.account import Account
from tests.conftest import assert_response_success, assert_response_error


class TestOrderEndpoints:
    """Test Order API Endpoints"""
    
    @pytest.fixture
    def test_order(self, db_session: Session, test_account: Account) -> Order:
        """Create test order in database"""
        order_data = {
            "ebay_order_id": "123456789-12345",
            "account_id": test_account.id,
            "user_id": test_account.user_id,
            "buyer_name": "John Doe",
            "buyer_email": "john@example.com",
            "buyer_username": "johndoe123",
            "subtotal": Decimal("100.00"),
            "shipping_cost": Decimal("10.00"),
            "tax_amount": Decimal("8.50"),
            "total_amount": Decimal("118.50"),
            "order_date": datetime.utcnow() - timedelta(days=1),
            "status": OrderStatus.PENDING,
            "payment_status": PaymentStatus.PENDING,
            "shipping_status": ShippingStatus.NOT_SHIPPED,
            "currency": "USD"
        }
        
        order = Order(**order_data)
        db_session.add(order)
        db_session.commit()
        db_session.refresh(order)
        
        return order
    
    @pytest.fixture
    def test_order_item(self, db_session: Session, test_order: Order) -> OrderItem:
        """Create test order item in database"""
        item_data = {
            "order_id": test_order.id,
            "ebay_item_id": "ITEM123456789",
            "sku": "SKU-TEST-001",
            "title": "Test Product - High Quality",
            "variation": "Size: Large, Color: Blue",
            "quantity": 2,
            "unit_price": Decimal("50.00"),
            "total_price": Decimal("100.00"),
            "status": "pending"
        }
        
        item = OrderItem(**item_data)
        db_session.add(item)
        db_session.commit()
        db_session.refresh(item)
        
        return item


class TestOrderCreation:
    """Test order creation endpoints"""
    
    def test_create_order_success(self, client: TestClient, auth_headers: dict, test_account: Account):
        """Test successful order creation"""
        order_data = {
            "ebay_order_id": "987654321-54321",
            "buyer_name": "Jane Smith",
            "buyer_email": "jane@example.com",
            "buyer_username": "janesmith456",
            "subtotal": 200.00,
            "shipping_cost": 15.00,
            "tax_amount": 17.25,
            "total_amount": 232.25,
            "currency": "USD",
            "order_items": [
                {
                    "ebay_item_id": "ITEM987654321",
                    "sku": "SKU-PREMIUM-001",
                    "title": "Premium Test Product",
                    "quantity": 1,
                    "unit_price": 200.00,
                    "total_price": 200.00
                }
            ]
        }
        
        response = client.post(
            f"/api/v1/orders/{test_account.id}",
            json=order_data,
            headers=auth_headers
        )
        
        data = assert_response_success(response, 201)
        assert data["ebay_order_id"] == "987654321-54321"
        assert data["buyer_name"] == "Jane Smith"
        assert data["total_amount"] == 232.25
        assert data["status"] == OrderStatus.PENDING.value
        assert len(data["order_items"]) == 1
    
    def test_create_order_duplicate_ebay_id(self, client: TestClient, auth_headers: dict, test_account: Account, test_order: Order):
        """Test creating order with duplicate eBay ID"""
        order_data = {
            "ebay_order_id": test_order.ebay_order_id,  # Duplicate ID
            "buyer_name": "Jane Smith",
            "buyer_email": "jane@example.com",
            "subtotal": 100.00,
            "total_amount": 100.00,
            "order_items": []
        }
        
        response = client.post(
            f"/api/v1/orders/{test_account.id}",
            json=order_data,
            headers=auth_headers
        )
        
        data = assert_response_error(response, 400)
        assert "already exists" in data["error"].lower()
    
    def test_create_order_invalid_data(self, client: TestClient, auth_headers: dict, test_account: Account):
        """Test creating order with invalid data"""
        order_data = {
            "ebay_order_id": "",  # Empty required field
            "buyer_name": "",     # Empty required field
            "total_amount": -100.00,  # Negative amount
            "order_items": []
        }
        
        response = client.post(
            f"/api/v1/orders/{test_account.id}",
            json=order_data,
            headers=auth_headers
        )
        
        assert_response_error(response, 422)  # Validation error
    
    def test_create_order_unauthorized(self, client: TestClient, test_account: Account):
        """Test creating order without authentication"""
        order_data = {
            "ebay_order_id": "UNAUTHORIZED-ORDER",
            "buyer_name": "Test User",
            "total_amount": 100.00,
            "order_items": []
        }
        
        response = client.post(
            f"/api/v1/orders/{test_account.id}",
            json=order_data
        )
        
        assert_response_error(response, 401)  # Unauthorized


class TestOrderRetrieval:
    """Test order retrieval endpoints"""
    
    def test_get_orders_list(self, client: TestClient, auth_headers: dict, test_account: Account, test_order: Order):
        """Test getting list of orders"""
        response = client.get(
            f"/api/v1/orders/{test_account.id}",
            headers=auth_headers
        )
        
        data = assert_response_success(response)
        assert "orders" in data
        assert "total" in data
        assert "page" in data
        assert "pages" in data
        assert len(data["orders"]) >= 1
        
        # Check first order
        order = data["orders"][0]
        assert order["id"] == test_order.id
        assert order["ebay_order_id"] == test_order.ebay_order_id
        assert order["buyer_name"] == test_order.buyer_name
    
    def test_get_orders_with_pagination(self, client: TestClient, auth_headers: dict, test_account: Account):
        """Test getting orders with pagination"""
        response = client.get(
            f"/api/v1/orders/{test_account.id}?page=1&limit=10",
            headers=auth_headers
        )
        
        data = assert_response_success(response)
        assert data["page"] == 1
        assert len(data["orders"]) <= 10
    
    def test_get_orders_with_status_filter(self, client: TestClient, auth_headers: dict, test_account: Account, test_order: Order):
        """Test getting orders with status filter"""
        response = client.get(
            f"/api/v1/orders/{test_account.id}?status={OrderStatus.PENDING.value}",
            headers=auth_headers
        )
        
        data = assert_response_success(response)
        for order in data["orders"]:
            assert order["status"] == OrderStatus.PENDING.value
    
    def test_get_order_by_id(self, client: TestClient, auth_headers: dict, test_account: Account, test_order: Order):
        """Test getting specific order by ID"""
        response = client.get(
            f"/api/v1/orders/{test_account.id}/{test_order.id}",
            headers=auth_headers
        )
        
        data = assert_response_success(response)
        assert data["id"] == test_order.id
        assert data["ebay_order_id"] == test_order.ebay_order_id
        assert data["buyer_name"] == test_order.buyer_name
        assert data["total_amount"] == float(test_order.total_amount)
    
    def test_get_order_by_id_not_found(self, client: TestClient, auth_headers: dict, test_account: Account):
        """Test getting non-existent order"""
        response = client.get(
            f"/api/v1/orders/{test_account.id}/999999",
            headers=auth_headers
        )
        
        data = assert_response_error(response, 404)
        assert "not found" in data["error"].lower()
    
    def test_get_order_wrong_account(self, client: TestClient, auth_headers: dict, test_order: Order):
        """Test getting order from wrong account"""
        wrong_account_id = 999
        response = client.get(
            f"/api/v1/orders/{wrong_account_id}/{test_order.id}",
            headers=auth_headers
        )
        
        data = assert_response_error(response, 404)


class TestOrderUpdates:
    """Test order update endpoints"""
    
    def test_update_order_status(self, client: TestClient, auth_headers: dict, test_account: Account, test_order: Order):
        """Test updating order status"""
        update_data = {
            "status": OrderStatus.CONFIRMED.value
        }
        
        response = client.patch(
            f"/api/v1/orders/{test_account.id}/{test_order.id}/status",
            json=update_data,
            headers=auth_headers
        )
        
        data = assert_response_success(response)
        assert data["status"] == OrderStatus.CONFIRMED.value
    
    def test_update_order_payment_info(self, client: TestClient, auth_headers: dict, test_account: Account, test_order: Order):
        """Test updating order payment information"""
        payment_data = {
            "payment_status": PaymentStatus.PAID.value,
            "payment_method": "PayPal",
            "payment_reference": "TXN123456789",
            "paid_amount": float(test_order.total_amount)
        }
        
        response = client.patch(
            f"/api/v1/orders/{test_account.id}/{test_order.id}/payment",
            json=payment_data,
            headers=auth_headers
        )
        
        data = assert_response_success(response)
        assert data["payment_status"] == PaymentStatus.PAID.value
        assert data["payment_method"] == "PayPal"
        assert data["payment_reference"] == "TXN123456789"
        assert data["paid_amount"] == float(test_order.total_amount)
    
    def test_update_order_shipping_info(self, client: TestClient, auth_headers: dict, test_account: Account, test_order: Order):
        """Test updating order shipping information"""
        shipping_data = {
            "shipping_method": "UPS Ground",
            "tracking_number": "1Z999999999999999999",
            "shipping_status": ShippingStatus.SHIPPED.value,
            "shipping_carrier": "UPS"
        }
        
        response = client.patch(
            f"/api/v1/orders/{test_account.id}/{test_order.id}/shipping",
            json=shipping_data,
            headers=auth_headers
        )
        
        data = assert_response_success(response)
        assert data["shipping_method"] == "UPS Ground"
        assert data["tracking_number"] == "1Z999999999999999999"
        assert data["shipping_status"] == ShippingStatus.SHIPPED.value
    
    def test_update_order_notes(self, client: TestClient, auth_headers: dict, test_account: Account, test_order: Order):
        """Test updating order notes"""
        notes_data = {
            "notes": "Customer requested express shipping",
            "internal_notes": "Handle with care - fragile items"
        }
        
        response = client.patch(
            f"/api/v1/orders/{test_account.id}/{test_order.id}/notes",
            json=notes_data,
            headers=auth_headers
        )
        
        data = assert_response_success(response)
        assert data["notes"] == "Customer requested express shipping"
        assert data["internal_notes"] == "Handle with care - fragile items"
    
    def test_update_order_invalid_status(self, client: TestClient, auth_headers: dict, test_account: Account, test_order: Order):
        """Test updating order with invalid status"""
        update_data = {
            "status": "INVALID_STATUS"
        }
        
        response = client.patch(
            f"/api/v1/orders/{test_account.id}/{test_order.id}/status",
            json=update_data,
            headers=auth_headers
        )
        
        assert_response_error(response, 422)  # Validation error


class TestOrderSearch:
    """Test order search endpoints"""
    
    def test_search_orders_by_buyer_name(self, client: TestClient, auth_headers: dict, test_account: Account, test_order: Order):
        """Test searching orders by buyer name"""
        response = client.get(
            f"/api/v1/orders/{test_account.id}/search?q={test_order.buyer_name}&type=buyer_name",
            headers=auth_headers
        )
        
        data = assert_response_success(response)
        assert len(data["orders"]) >= 1
        assert any(order["buyer_name"] == test_order.buyer_name for order in data["orders"])
    
    def test_search_orders_by_ebay_order_id(self, client: TestClient, auth_headers: dict, test_account: Account, test_order: Order):
        """Test searching orders by eBay order ID"""
        response = client.get(
            f"/api/v1/orders/{test_account.id}/search?q={test_order.ebay_order_id}&type=ebay_order_id",
            headers=auth_headers
        )
        
        data = assert_response_success(response)
        assert len(data["orders"]) == 1
        assert data["orders"][0]["ebay_order_id"] == test_order.ebay_order_id
    
    def test_search_orders_by_buyer_email(self, client: TestClient, auth_headers: dict, test_account: Account, test_order: Order):
        """Test searching orders by buyer email"""
        response = client.get(
            f"/api/v1/orders/{test_account.id}/search?q={test_order.buyer_email}&type=buyer_email",
            headers=auth_headers
        )
        
        data = assert_response_success(response)
        assert len(data["orders"]) >= 1
        assert any(order["buyer_email"] == test_order.buyer_email for order in data["orders"])
    
    def test_search_orders_no_results(self, client: TestClient, auth_headers: dict, test_account: Account):
        """Test searching with no matching results"""
        response = client.get(
            f"/api/v1/orders/{test_account.id}/search?q=nonexistentorder&type=ebay_order_id",
            headers=auth_headers
        )
        
        data = assert_response_success(response)
        assert len(data["orders"]) == 0
        assert data["total"] == 0


class TestOrderItems:
    """Test order items endpoints"""
    
    def test_get_order_items(self, client: TestClient, auth_headers: dict, test_account: Account, test_order: Order, test_order_item: OrderItem):
        """Test getting order items"""
        response = client.get(
            f"/api/v1/orders/{test_account.id}/{test_order.id}/items",
            headers=auth_headers
        )
        
        data = assert_response_success(response)
        assert len(data["items"]) >= 1
        
        item = data["items"][0]
        assert item["id"] == test_order_item.id
        assert item["ebay_item_id"] == test_order_item.ebay_item_id
        assert item["sku"] == test_order_item.sku
        assert item["title"] == test_order_item.title
        assert item["quantity"] == test_order_item.quantity
    
    def test_update_order_item(self, client: TestClient, auth_headers: dict, test_account: Account, test_order: Order, test_order_item: OrderItem):
        """Test updating order item"""
        update_data = {
            "quantity": 3,
            "notes": "Quantity updated per customer request"
        }
        
        response = client.patch(
            f"/api/v1/orders/{test_account.id}/{test_order.id}/items/{test_order_item.id}",
            json=update_data,
            headers=auth_headers
        )
        
        data = assert_response_success(response)
        assert data["quantity"] == 3
        assert data["notes"] == "Quantity updated per customer request"


class TestOrderStatistics:
    """Test order statistics endpoints"""
    
    def test_get_order_statistics(self, client: TestClient, auth_headers: dict, test_account: Account, test_order: Order):
        """Test getting order statistics"""
        response = client.get(
            f"/api/v1/orders/{test_account.id}/statistics",
            headers=auth_headers
        )
        
        data = assert_response_success(response)
        assert "total_orders" in data
        assert "total_revenue" in data
        assert "average_order_value" in data
        assert "orders_by_status" in data
        assert data["total_orders"] >= 1
    
    def test_get_order_statistics_with_date_range(self, client: TestClient, auth_headers: dict, test_account: Account):
        """Test getting order statistics with date range"""
        start_date = (datetime.utcnow() - timedelta(days=30)).date()
        end_date = datetime.utcnow().date()
        
        response = client.get(
            f"/api/v1/orders/{test_account.id}/statistics?start_date={start_date}&end_date={end_date}",
            headers=auth_headers
        )
        
        data = assert_response_success(response)
        assert "total_orders" in data
        assert "total_revenue" in data


class TestOrderAnalytics:
    """Test order analytics endpoints"""
    
    def test_get_dashboard_stats(self, client: TestClient, auth_headers: dict, test_account: Account):
        """Test getting dashboard statistics"""
        response = client.get(
            f"/api/v1/orders/{test_account.id}/analytics/dashboard",
            headers=auth_headers
        )
        
        data = assert_response_success(response)
        assert "total_orders" in data
        assert "total_revenue" in data
        assert "status_distribution" in data
        assert "trends" in data
        assert "performance_metrics" in data
    
    def test_get_revenue_analysis(self, client: TestClient, auth_headers: dict, test_account: Account):
        """Test getting revenue analysis"""
        response = client.get(
            f"/api/v1/orders/{test_account.id}/analytics/revenue?period=monthly",
            headers=auth_headers
        )
        
        data = assert_response_success(response)
        assert "period" in data
        assert "revenue_timeline" in data
        assert "growth_analysis" in data
        assert "total_revenue" in data
    
    def test_get_performance_report(self, client: TestClient, auth_headers: dict, test_account: Account):
        """Test getting performance report"""
        response = client.get(
            f"/api/v1/orders/{test_account.id}/analytics/performance",
            headers=auth_headers
        )
        
        data = assert_response_success(response)
        assert "average_processing_time_hours" in data
        assert "fulfillment_rate_percentage" in data
        assert "on_time_shipping_percentage" in data
        assert "recommendations" in data


class TestOrderWorkflow:
    """Test order workflow endpoints"""
    
    def test_run_order_workflows(self, client: TestClient, auth_headers: dict, test_account: Account):
        """Test running order workflows"""
        response = client.post(
            f"/api/v1/orders/{test_account.id}/workflow/run",
            headers=auth_headers
        )
        
        data = assert_response_success(response)
        assert "processed_orders" in data
        assert "status_updates" in data
        assert "overdue_flagged" in data
        assert "auto_completed" in data
    
    def test_get_workflow_summary(self, client: TestClient, auth_headers: dict, test_account: Account):
        """Test getting workflow summary"""
        response = client.get(
            f"/api/v1/orders/{test_account.id}/workflow/summary",
            headers=auth_headers
        )
        
        data = assert_response_success(response)
        assert "status_distribution" in data
        assert "overdue_orders" in data
        assert "priority_orders" in data
        assert "workflow_rules_active" in data


class TestOrderBulkOperations:
    """Test bulk order operations"""
    
    def test_bulk_update_status(self, client: TestClient, auth_headers: dict, test_account: Account, test_order: Order):
        """Test bulk status update"""
        update_data = {
            "order_ids": [test_order.id],
            "status": OrderStatus.CONFIRMED.value
        }
        
        response = client.patch(
            f"/api/v1/orders/{test_account.id}/bulk/status",
            json=update_data,
            headers=auth_headers
        )
        
        data = assert_response_success(response)
        assert "updated_count" in data
        assert data["updated_count"] >= 1
    
    def test_bulk_export(self, client: TestClient, auth_headers: dict, test_account: Account):
        """Test bulk order export"""
        response = client.get(
            f"/api/v1/orders/{test_account.id}/export?format=csv",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv"


class TestOrderFiltering:
    """Test advanced order filtering"""
    
    def test_filter_by_date_range(self, client: TestClient, auth_headers: dict, test_account: Account):
        """Test filtering orders by date range"""
        start_date = (datetime.utcnow() - timedelta(days=7)).date()
        end_date = datetime.utcnow().date()
        
        response = client.get(
            f"/api/v1/orders/{test_account.id}?start_date={start_date}&end_date={end_date}",
            headers=auth_headers
        )
        
        data = assert_response_success(response)
        # Verify all returned orders are within date range
        for order in data["orders"]:
            order_date = datetime.fromisoformat(order["order_date"].replace('Z', '+00:00')).date()
            assert start_date <= order_date <= end_date
    
    def test_filter_by_multiple_statuses(self, client: TestClient, auth_headers: dict, test_account: Account):
        """Test filtering by multiple order statuses"""
        statuses = f"{OrderStatus.PENDING.value},{OrderStatus.CONFIRMED.value}"
        
        response = client.get(
            f"/api/v1/orders/{test_account.id}?status={statuses}",
            headers=auth_headers
        )
        
        data = assert_response_success(response)
        for order in data["orders"]:
            assert order["status"] in [OrderStatus.PENDING.value, OrderStatus.CONFIRMED.value]
    
    def test_filter_by_payment_status(self, client: TestClient, auth_headers: dict, test_account: Account):
        """Test filtering by payment status"""
        response = client.get(
            f"/api/v1/orders/{test_account.id}?payment_status={PaymentStatus.PENDING.value}",
            headers=auth_headers
        )
        
        data = assert_response_success(response)
        for order in data["orders"]:
            assert order["payment_status"] == PaymentStatus.PENDING.value


class TestOrderSorting:
    """Test order sorting functionality"""
    
    def test_sort_by_order_date(self, client: TestClient, auth_headers: dict, test_account: Account):
        """Test sorting orders by order date"""
        response = client.get(
            f"/api/v1/orders/{test_account.id}?sort=order_date&order=desc",
            headers=auth_headers
        )
        
        data = assert_response_success(response)
        if len(data["orders"]) > 1:
            # Verify descending order
            dates = [datetime.fromisoformat(order["order_date"].replace('Z', '+00:00')) for order in data["orders"]]
            assert dates == sorted(dates, reverse=True)
    
    def test_sort_by_total_amount(self, client: TestClient, auth_headers: dict, test_account: Account):
        """Test sorting orders by total amount"""
        response = client.get(
            f"/api/v1/orders/{test_account.id}?sort=total_amount&order=asc",
            headers=auth_headers
        )
        
        data = assert_response_success(response)
        if len(data["orders"]) > 1:
            # Verify ascending order
            amounts = [order["total_amount"] for order in data["orders"]]
            assert amounts == sorted(amounts)


class TestErrorHandling:
    """Test error handling in order endpoints"""
    
    def test_invalid_account_id(self, client: TestClient, auth_headers: dict):
        """Test accessing orders with invalid account ID"""
        response = client.get(
            "/api/v1/orders/invalid_id",
            headers=auth_headers
        )
        
        assert_response_error(response, 422)  # Validation error for invalid ID format
    
    def test_nonexistent_account_id(self, client: TestClient, auth_headers: dict):
        """Test accessing orders with non-existent account ID"""
        response = client.get(
            "/api/v1/orders/999999",
            headers=auth_headers
        )
        
        assert_response_error(response, 404)  # Account not found
    
    def test_invalid_order_data_types(self, client: TestClient, auth_headers: dict, test_account: Account):
        """Test creating order with invalid data types"""
        order_data = {
            "ebay_order_id": "VALID-ORDER-ID",
            "buyer_name": "Valid Name",
            "buyer_email": "valid@email.com",
            "total_amount": "invalid_amount",  # Should be number
            "order_items": []
        }
        
        response = client.post(
            f"/api/v1/orders/{test_account.id}",
            json=order_data,
            headers=auth_headers
        )
        
        assert_response_error(response, 422)  # Validation error
    
    def test_missing_required_fields(self, client: TestClient, auth_headers: dict, test_account: Account):
        """Test creating order with missing required fields"""
        order_data = {
            # Missing required fields like ebay_order_id, buyer_name, etc.
            "total_amount": 100.00
        }
        
        response = client.post(
            f"/api/v1/orders/{test_account.id}",
            json=order_data,
            headers=auth_headers
        )
        
        assert_response_error(response, 422)  # Validation error


class TestOrderPermissions:
    """Test order access permissions"""
    
    def test_user_cannot_access_other_accounts(self, client: TestClient, auth_headers: dict):
        """Test that regular users cannot access orders from other accounts"""
        # Assuming auth_headers is for a regular user, not admin
        other_account_id = 999  # Non-existent or unauthorized account
        
        response = client.get(
            f"/api/v1/orders/{other_account_id}",
            headers=auth_headers
        )
        
        # Should return 404 (not found) or 403 (forbidden)
        assert response.status_code in [403, 404]
    
    def test_admin_can_access_all_accounts(self, client: TestClient, admin_headers: dict, test_account: Account):
        """Test that admin users can access orders from any account"""
        response = client.get(
            f"/api/v1/orders/{test_account.id}",
            headers=admin_headers
        )
        
        # Admin should be able to access any account's orders
        data = assert_response_success(response)
        assert "orders" in data