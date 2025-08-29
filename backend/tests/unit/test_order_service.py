"""
Unit tests for Order Service
Following SOLID principles for comprehensive testing
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session

from app.services.order_service import OrderService
from app.models.order import Order, OrderItem, OrderStatus, PaymentStatus, ShippingStatus
from app.models.user import User
from app.models.account import Account
from app.core.exceptions import EbayManagerException, ValidationException, NotFoundError


class TestOrderService:
    """Test Order Service following SOLID principles"""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        return Mock(spec=Session)
    
    @pytest.fixture
    def order_service(self, mock_db):
        """Create OrderService instance with mocked dependencies"""
        return OrderService(mock_db)
    
    @pytest.fixture
    def sample_order_data(self):
        """Sample order data for testing"""
        return {
            "ebay_order_id": "123456789-12345",
            "account_id": 1,
            "user_id": 1,
            "buyer_name": "John Doe",
            "buyer_email": "john@example.com",
            "subtotal": Decimal("100.00"),
            "shipping_cost": Decimal("10.00"),
            "tax_amount": Decimal("8.50"),
            "total_amount": Decimal("118.50"),
            "order_date": datetime.utcnow(),
            "status": OrderStatus.PENDING,
            "payment_status": PaymentStatus.PENDING,
            "shipping_status": ShippingStatus.NOT_SHIPPED
        }
    
    @pytest.fixture
    def sample_order_item_data(self):
        """Sample order item data for testing"""
        return {
            "ebay_item_id": "ITEM123456",
            "sku": "SKU123",
            "title": "Test Product",
            "quantity": 2,
            "unit_price": Decimal("50.00"),
            "total_price": Decimal("100.00")
        }


class TestOrderCreation:
    """Test order creation functionality"""
    
    def test_create_order_success(self, order_service, mock_db, sample_order_data, sample_order_item_data):
        """Test successful order creation"""
        # Arrange
        order_items = [sample_order_item_data]
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None
        
        # Mock the order creation
        created_order = Order(**sample_order_data)
        created_order.id = 1
        
        with patch.object(Order, '__init__', return_value=None):
            with patch.object(order_service, '_validate_order_data'):
                with patch.object(order_service, '_create_order_items'):
                    # Act
                    result = order_service.create_order(
                        order_data=sample_order_data,
                        order_items=order_items,
                        account_id=1,
                        user_id=1
                    )
        
        # Assert
        mock_db.add.assert_called()
        mock_db.commit.assert_called()
        assert order_service._validate_order_data.called
        assert order_service._create_order_items.called
    
    def test_create_order_validation_error(self, order_service, sample_order_data):
        """Test order creation with validation error"""
        # Arrange
        invalid_data = sample_order_data.copy()
        invalid_data["total_amount"] = Decimal("-10.00")  # Invalid negative amount
        
        with patch.object(order_service, '_validate_order_data', side_effect=ValidationException("Invalid total amount")):
            # Act & Assert
            with pytest.raises(ValidationException):
                order_service.create_order(
                    order_data=invalid_data,
                    order_items=[],
                    account_id=1,
                    user_id=1
                )
    
    def test_create_order_duplicate_ebay_id(self, order_service, mock_db, sample_order_data):
        """Test order creation with duplicate eBay ID"""
        # Arrange
        existing_order = Mock()
        mock_db.query().filter().first.return_value = existing_order
        
        # Act & Assert
        with pytest.raises(ValidationException, match="Order with this eBay ID already exists"):
            order_service.create_order(
                order_data=sample_order_data,
                order_items=[],
                account_id=1,
                user_id=1
            )


class TestOrderRetrieval:
    """Test order retrieval functionality"""
    
    def test_get_order_by_id_success(self, order_service, mock_db, sample_order_data):
        """Test successful order retrieval by ID"""
        # Arrange
        order = Order(**sample_order_data)
        order.id = 1
        mock_db.query().filter().first.return_value = order
        
        # Act
        result = order_service.get_order_by_id(order_id=1, account_id=1, user_id=1)
        
        # Assert
        assert result == order
        mock_db.query.assert_called_once()
    
    def test_get_order_by_id_not_found(self, order_service, mock_db):
        """Test order retrieval when order doesn't exist"""
        # Arrange
        mock_db.query().filter().first.return_value = None
        
        # Act & Assert
        with pytest.raises(NotFoundError, match="Order not found"):
            order_service.get_order_by_id(order_id=999, account_id=1, user_id=1)
    
    def test_get_orders_list(self, order_service, mock_db, sample_order_data):
        """Test getting list of orders with pagination"""
        # Arrange
        orders = [Order(**sample_order_data) for _ in range(5)]
        mock_query = Mock()
        mock_query.offset().limit().all.return_value = orders
        mock_query.count.return_value = 5
        mock_db.query.return_value = mock_query
        
        # Act
        result = order_service.get_orders(
            account_id=1, 
            user_id=1, 
            skip=0, 
            limit=10,
            status_filter=None
        )
        
        # Assert
        assert "orders" in result
        assert "total" in result
        assert "page" in result
        assert "pages" in result
        assert len(result["orders"]) == 5
        assert result["total"] == 5


class TestOrderUpdate:
    """Test order update functionality"""
    
    def test_update_order_status_success(self, order_service, mock_db, sample_order_data):
        """Test successful order status update"""
        # Arrange
        order = Order(**sample_order_data)
        order.id = 1
        mock_db.query().filter().first.return_value = order
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None
        
        # Act
        result = order_service.update_order_status(
            order_id=1,
            status=OrderStatus.CONFIRMED,
            account_id=1,
            user_id=1
        )
        
        # Assert
        assert result.status == OrderStatus.CONFIRMED
        mock_db.commit.assert_called_once()
    
    def test_update_order_payment_info(self, order_service, mock_db, sample_order_data):
        """Test updating order payment information"""
        # Arrange
        order = Order(**sample_order_data)
        order.id = 1
        mock_db.query().filter().first.return_value = order
        mock_db.commit.return_value = None
        
        payment_data = {
            "payment_status": PaymentStatus.PAID,
            "payment_method": "PayPal",
            "payment_reference": "TXN123456",
            "paid_amount": Decimal("118.50")
        }
        
        # Act
        result = order_service.update_payment_info(
            order_id=1,
            payment_data=payment_data,
            account_id=1,
            user_id=1
        )
        
        # Assert
        assert result.payment_status == PaymentStatus.PAID
        assert result.payment_method == "PayPal"
        assert result.paid_amount == Decimal("118.50")
        mock_db.commit.assert_called_once()
    
    def test_update_shipping_info(self, order_service, mock_db, sample_order_data):
        """Test updating order shipping information"""
        # Arrange
        order = Order(**sample_order_data)
        order.id = 1
        mock_db.query().filter().first.return_value = order
        mock_db.commit.return_value = None
        
        shipping_data = {
            "shipping_method": "UPS Ground",
            "tracking_number": "1Z999999999999999999",
            "shipping_status": ShippingStatus.SHIPPED,
            "shipping_date": datetime.utcnow()
        }
        
        # Act
        result = order_service.update_shipping_info(
            order_id=1,
            shipping_data=shipping_data,
            account_id=1,
            user_id=1
        )
        
        # Assert
        assert result.shipping_method == "UPS Ground"
        assert result.tracking_number == "1Z999999999999999999"
        assert result.shipping_status == ShippingStatus.SHIPPED
        mock_db.commit.assert_called_once()


class TestOrderSearch:
    """Test order search and filtering functionality"""
    
    def test_search_orders_by_buyer_name(self, order_service, mock_db, sample_order_data):
        """Test searching orders by buyer name"""
        # Arrange
        orders = [Order(**sample_order_data)]
        mock_query = Mock()
        mock_query.filter().offset().limit().all.return_value = orders
        mock_query.filter().count.return_value = 1
        mock_db.query.return_value = mock_query
        
        # Act
        result = order_service.search_orders(
            account_id=1,
            user_id=1,
            search_term="John Doe",
            search_type="buyer_name"
        )
        
        # Assert
        assert len(result["orders"]) == 1
        assert result["total"] == 1
    
    def test_filter_orders_by_status(self, order_service, mock_db, sample_order_data):
        """Test filtering orders by status"""
        # Arrange
        orders = [Order(**sample_order_data)]
        mock_query = Mock()
        mock_query.filter().offset().limit().all.return_value = orders
        mock_query.filter().count.return_value = 1
        mock_db.query.return_value = mock_query
        
        # Act
        result = order_service.get_orders(
            account_id=1,
            user_id=1,
            status_filter=OrderStatus.PENDING
        )
        
        # Assert
        assert len(result["orders"]) == 1
    
    def test_filter_orders_by_date_range(self, order_service, mock_db, sample_order_data):
        """Test filtering orders by date range"""
        # Arrange
        orders = [Order(**sample_order_data)]
        mock_query = Mock()
        mock_query.filter().offset().limit().all.return_value = orders
        mock_query.filter().count.return_value = 1
        mock_db.query.return_value = mock_query
        
        start_date = datetime.utcnow() - timedelta(days=30)
        end_date = datetime.utcnow()
        
        # Act
        result = order_service.get_orders_by_date_range(
            account_id=1,
            user_id=1,
            start_date=start_date,
            end_date=end_date
        )
        
        # Assert
        assert len(result["orders"]) == 1


class TestOrderValidation:
    """Test order validation functionality"""
    
    def test_validate_order_data_success(self, order_service, sample_order_data):
        """Test successful order data validation"""
        # Act & Assert - should not raise any exception
        order_service._validate_order_data(sample_order_data)
    
    def test_validate_order_data_negative_amount(self, order_service, sample_order_data):
        """Test validation with negative total amount"""
        # Arrange
        sample_order_data["total_amount"] = Decimal("-10.00")
        
        # Act & Assert
        with pytest.raises(ValidationException, match="Total amount must be positive"):
            order_service._validate_order_data(sample_order_data)
    
    def test_validate_order_data_missing_ebay_id(self, order_service, sample_order_data):
        """Test validation with missing eBay order ID"""
        # Arrange
        del sample_order_data["ebay_order_id"]
        
        # Act & Assert
        with pytest.raises(ValidationException, match="eBay order ID is required"):
            order_service._validate_order_data(sample_order_data)
    
    def test_validate_order_financial_consistency(self, order_service, sample_order_data):
        """Test validation of financial data consistency"""
        # Arrange
        sample_order_data["subtotal"] = Decimal("100.00")
        sample_order_data["shipping_cost"] = Decimal("10.00")
        sample_order_data["tax_amount"] = Decimal("8.50")
        sample_order_data["total_amount"] = Decimal("200.00")  # Inconsistent total
        
        # Act & Assert
        with pytest.raises(ValidationException, match="Total amount does not match"):
            order_service._validate_financial_consistency(sample_order_data)


class TestOrderStatistics:
    """Test order statistics and reporting functionality"""
    
    def test_get_order_statistics(self, order_service, mock_db):
        """Test getting order statistics"""
        # Arrange
        mock_result = Mock()
        mock_result.total_orders = 100
        mock_result.total_revenue = Decimal("10000.00")
        mock_result.avg_order_value = Decimal("100.00")
        
        mock_db.query().filter().first.return_value = mock_result
        
        # Act
        result = order_service.get_order_statistics(
            account_id=1,
            user_id=1,
            date_range=30
        )
        
        # Assert
        assert "total_orders" in result
        assert "total_revenue" in result
        assert "average_order_value" in result
    
    def test_get_orders_by_status_count(self, order_service, mock_db):
        """Test getting order counts by status"""
        # Arrange
        status_counts = [
            (OrderStatus.PENDING, 10),
            (OrderStatus.CONFIRMED, 25),
            (OrderStatus.SHIPPED, 50),
            (OrderStatus.DELIVERED, 15)
        ]
        mock_db.query().group_by().all.return_value = status_counts
        
        # Act
        result = order_service.get_orders_by_status_count(
            account_id=1,
            user_id=1
        )
        
        # Assert
        assert result[str(OrderStatus.PENDING)] == 10
        assert result[str(OrderStatus.CONFIRMED)] == 25
        assert result[str(OrderStatus.SHIPPED)] == 50
        assert result[str(OrderStatus.DELIVERED)] == 15


class TestErrorHandling:
    """Test error handling in OrderService"""
    
    def test_database_error_handling(self, order_service, mock_db, sample_order_data):
        """Test handling of database errors"""
        # Arrange
        mock_db.commit.side_effect = Exception("Database connection error")
        mock_db.rollback.return_value = None
        
        # Act & Assert
        with pytest.raises(EbayManagerException, match="Failed to create order"):
            order_service.create_order(
                order_data=sample_order_data,
                order_items=[],
                account_id=1,
                user_id=1
            )
        
        mock_db.rollback.assert_called_once()
    
    def test_permission_validation(self, order_service, mock_db, sample_order_data):
        """Test user permission validation"""
        # Arrange - Mock user without access to account
        mock_user = Mock()
        mock_user.id = 2
        mock_user.role = "user"
        mock_db.query().filter().first.return_value = mock_user
        
        # Act & Assert
        with pytest.raises(EbayManagerException, match="Access denied"):
            order_service._validate_user_access(account_id=1, user_id=2)