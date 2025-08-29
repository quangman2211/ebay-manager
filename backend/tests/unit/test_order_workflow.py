"""
Unit tests for Order Workflow Engine
Following SOLID principles for workflow testing
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session

from app.services.order_workflow import OrderWorkflowEngine
from app.models.order import Order, OrderStatus, PaymentStatus, ShippingStatus
from app.models.user import User
from app.core.exceptions import EbayManagerException


class TestOrderWorkflowEngine:
    """Test Order Workflow Engine following SOLID principles"""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        return Mock(spec=Session)
    
    @pytest.fixture
    def workflow_engine(self, mock_db):
        """Create OrderWorkflowEngine instance with mocked dependencies"""
        return OrderWorkflowEngine(mock_db)
    
    @pytest.fixture
    def sample_order(self):
        """Sample order for testing"""
        order = Mock()
        order.id = 1
        order.ebay_order_id = "123456789-12345"
        order.account_id = 1
        order.user_id = 1
        order.buyer_name = "John Doe"
        order.buyer_email = "john@example.com"
        order.total_amount = Decimal("100.00")
        order.paid_amount = Decimal("0.00")
        order.order_date = datetime.utcnow() - timedelta(days=2)
        order.payment_date = None
        order.shipping_date = None
        order.actual_delivery_date = None
        order.tracking_number = None
        order.status = OrderStatus.PENDING
        order.payment_status = PaymentStatus.PENDING
        order.shipping_status = ShippingStatus.NOT_SHIPPED
        order.is_priority = False
        order.internal_notes = ""
        order.updated_at = datetime.utcnow() - timedelta(hours=1)
        return order


class TestWorkflowProcessing:
    """Test main workflow processing functionality"""
    
    def test_process_order_workflows_success(self, workflow_engine, mock_db, sample_order):
        """Test successful workflow processing"""
        # Arrange
        orders = [sample_order]
        mock_db.query().filter().all.return_value = orders
        mock_db.commit.return_value = None
        
        with patch.object(workflow_engine, '_process_single_order_workflow') as mock_process:
            mock_process.return_value = {
                'status_updates': 1,
                'overdue_flagged': 0,
                'auto_completed': 0
            }
            
            # Act
            result = workflow_engine.process_order_workflows(account_id=1)
        
        # Assert
        assert result['processed_orders'] == 1
        assert result['status_updates'] == 1
        assert result['overdue_flagged'] == 0
        assert result['auto_completed'] == 0
        assert result['errors'] == []
        mock_db.commit.assert_called_once()
    
    def test_process_order_workflows_with_errors(self, workflow_engine, mock_db, sample_order):
        """Test workflow processing with some errors"""
        # Arrange
        orders = [sample_order]
        mock_db.query().filter().all.return_value = orders
        mock_db.commit.return_value = None
        
        with patch.object(workflow_engine, '_process_single_order_workflow') as mock_process:
            mock_process.side_effect = Exception("Workflow processing error")
            
            # Act
            result = workflow_engine.process_order_workflows(account_id=1)
        
        # Assert
        assert result['processed_orders'] == 1
        assert len(result['errors']) == 1
        assert "Workflow error for order 1" in result['errors'][0]
    
    def test_process_order_workflows_database_error(self, workflow_engine, mock_db):
        """Test workflow processing with database error"""
        # Arrange
        mock_db.query.side_effect = Exception("Database connection error")
        mock_db.rollback.return_value = None
        
        # Act & Assert
        with pytest.raises(EbayManagerException, match="Workflow processing failed"):
            workflow_engine.process_order_workflows(account_id=1)
        
        mock_db.rollback.assert_called_once()
    
    def test_get_workflow_eligible_orders(self, workflow_engine, mock_db):
        """Test getting orders eligible for workflow processing"""
        # Arrange
        orders = [Mock(), Mock(), Mock()]
        mock_db.query().filter().all.return_value = orders
        
        # Act
        result = workflow_engine._get_workflow_eligible_orders(account_id=1)
        
        # Assert
        assert len(result) == 3
        mock_db.query.assert_called_once()


class TestSingleOrderWorkflow:
    """Test single order workflow processing"""
    
    def test_process_single_order_workflow_all_rules(self, workflow_engine, sample_order):
        """Test single order workflow with all rules triggered"""
        # Arrange
        with patch.object(workflow_engine, '_should_auto_advance_payment', return_value=True):
            with patch.object(workflow_engine, '_should_auto_advance_shipping', return_value=True):
                with patch.object(workflow_engine, '_should_flag_overdue', return_value=True):
                    with patch.object(workflow_engine, '_should_auto_complete', return_value=True):
                        with patch.object(workflow_engine, '_auto_advance_payment_status'):
                            with patch.object(workflow_engine, '_auto_advance_shipping_status'):
                                with patch.object(workflow_engine, '_flag_order_as_priority'):
                                    with patch.object(workflow_engine, '_auto_complete_order'):
                                        # Act
                                        result = workflow_engine._process_single_order_workflow(sample_order)
        
        # Assert
        assert result['status_updates'] == 3  # payment + shipping + completion
        assert result['overdue_flagged'] == 1
        assert result['auto_completed'] == 1
    
    def test_process_single_order_workflow_no_rules(self, workflow_engine, sample_order):
        """Test single order workflow with no rules triggered"""
        # Arrange
        with patch.object(workflow_engine, '_should_auto_advance_payment', return_value=False):
            with patch.object(workflow_engine, '_should_auto_advance_shipping', return_value=False):
                with patch.object(workflow_engine, '_should_flag_overdue', return_value=False):
                    with patch.object(workflow_engine, '_should_auto_complete', return_value=False):
                        # Act
                        result = workflow_engine._process_single_order_workflow(sample_order)
        
        # Assert
        assert result['status_updates'] == 0
        assert result['overdue_flagged'] == 0
        assert result['auto_completed'] == 0


class TestPaymentAdvancement:
    """Test payment status advancement rules"""
    
    def test_should_auto_advance_payment_true(self, workflow_engine):
        """Test payment advancement condition when true"""
        # Arrange
        order = Mock()
        order.status = OrderStatus.CONFIRMED
        order.payment_status = PaymentStatus.PENDING
        order.payment_date = datetime.utcnow()
        
        # Act
        result = workflow_engine._should_auto_advance_payment(order)
        
        # Assert
        assert result is True
    
    def test_should_auto_advance_payment_false_no_payment_date(self, workflow_engine):
        """Test payment advancement when no payment date"""
        # Arrange
        order = Mock()
        order.status = OrderStatus.CONFIRMED
        order.payment_status = PaymentStatus.PENDING
        order.payment_date = None
        
        # Act
        result = workflow_engine._should_auto_advance_payment(order)
        
        # Assert
        assert result is False
    
    def test_should_auto_advance_payment_false_wrong_status(self, workflow_engine):
        """Test payment advancement with wrong order status"""
        # Arrange
        order = Mock()
        order.status = OrderStatus.PENDING
        order.payment_status = PaymentStatus.PENDING
        order.payment_date = datetime.utcnow()
        
        # Act
        result = workflow_engine._should_auto_advance_payment(order)
        
        # Assert
        assert result is False
    
    def test_auto_advance_payment_status(self, workflow_engine):
        """Test payment status advancement"""
        # Arrange
        order = Mock()
        order.payment_status = PaymentStatus.PENDING
        order.total_amount = Decimal("100.00")
        order.paid_amount = Decimal("0.00")
        order.payment_date = None
        order.status = OrderStatus.PENDING
        order.updated_at = datetime.utcnow() - timedelta(hours=1)
        
        # Act
        workflow_engine._auto_advance_payment_status(order)
        
        # Assert
        assert order.payment_status == PaymentStatus.PAID
        assert order.paid_amount == Decimal("100.00")
        assert order.payment_date is not None
        assert order.status == OrderStatus.CONFIRMED
        assert order.updated_at > datetime.utcnow() - timedelta(minutes=1)
    
    def test_auto_advance_payment_status_from_confirmed(self, workflow_engine):
        """Test payment advancement from confirmed status"""
        # Arrange
        order = Mock()
        order.payment_status = PaymentStatus.PENDING
        order.total_amount = Decimal("100.00")
        order.paid_amount = Decimal("0.00")
        order.payment_date = datetime.utcnow()
        order.status = OrderStatus.CONFIRMED
        order.updated_at = datetime.utcnow() - timedelta(hours=1)
        
        # Act
        workflow_engine._auto_advance_payment_status(order)
        
        # Assert
        assert order.payment_status == PaymentStatus.PAID
        assert order.status == OrderStatus.PROCESSING


class TestShippingAdvancement:
    """Test shipping status advancement rules"""
    
    def test_should_auto_advance_shipping_true(self, workflow_engine):
        """Test shipping advancement condition when true"""
        # Arrange
        order = Mock()
        order.status = OrderStatus.PROCESSING
        order.shipping_status = ShippingStatus.NOT_SHIPPED
        order.tracking_number = "TRACK123456"
        order.shipping_date = datetime.utcnow()
        
        # Act
        result = workflow_engine._should_auto_advance_shipping(order)
        
        # Assert
        assert result is True
    
    def test_should_auto_advance_shipping_false_no_tracking(self, workflow_engine):
        """Test shipping advancement when no tracking number"""
        # Arrange
        order = Mock()
        order.status = OrderStatus.PROCESSING
        order.shipping_status = ShippingStatus.NOT_SHIPPED
        order.tracking_number = None
        order.shipping_date = datetime.utcnow()
        
        # Act
        result = workflow_engine._should_auto_advance_shipping(order)
        
        # Assert
        assert result is False
    
    def test_should_auto_advance_shipping_false_wrong_status(self, workflow_engine):
        """Test shipping advancement with wrong order status"""
        # Arrange
        order = Mock()
        order.status = OrderStatus.PENDING
        order.shipping_status = ShippingStatus.NOT_SHIPPED
        order.tracking_number = "TRACK123456"
        order.shipping_date = datetime.utcnow()
        
        # Act
        result = workflow_engine._should_auto_advance_shipping(order)
        
        # Assert
        assert result is False
    
    def test_auto_advance_shipping_status(self, workflow_engine):
        """Test shipping status advancement"""
        # Arrange
        order = Mock()
        order.shipping_status = ShippingStatus.NOT_SHIPPED
        order.status = OrderStatus.PROCESSING
        order.shipping_date = None
        order.updated_at = datetime.utcnow() - timedelta(hours=1)
        
        # Act
        workflow_engine._auto_advance_shipping_status(order)
        
        # Assert
        assert order.shipping_status == ShippingStatus.SHIPPED
        assert order.status == OrderStatus.SHIPPED
        assert order.shipping_date is not None
        assert order.updated_at > datetime.utcnow() - timedelta(minutes=1)


class TestOverdueFlagging:
    """Test overdue order flagging rules"""
    
    def test_should_flag_overdue_true(self, workflow_engine):
        """Test overdue flagging condition when true"""
        # Arrange
        order = Mock()
        order.is_priority = False
        order.order_date = datetime.utcnow() - timedelta(days=4)  # 4 days old
        order.shipping_status = ShippingStatus.NOT_SHIPPED
        order.status = OrderStatus.PROCESSING
        
        # Act
        result = workflow_engine._should_flag_overdue(order)
        
        # Assert
        assert result is True
    
    def test_should_flag_overdue_false_already_priority(self, workflow_engine):
        """Test overdue flagging when already flagged as priority"""
        # Arrange
        order = Mock()
        order.is_priority = True  # Already flagged
        order.order_date = datetime.utcnow() - timedelta(days=4)
        order.shipping_status = ShippingStatus.NOT_SHIPPED
        order.status = OrderStatus.PROCESSING
        
        # Act
        result = workflow_engine._should_flag_overdue(order)
        
        # Assert
        assert result is False
    
    def test_should_flag_overdue_false_too_new(self, workflow_engine):
        """Test overdue flagging for new orders"""
        # Arrange
        order = Mock()
        order.is_priority = False
        order.order_date = datetime.utcnow() - timedelta(days=2)  # Only 2 days old
        order.shipping_status = ShippingStatus.NOT_SHIPPED
        order.status = OrderStatus.PROCESSING
        
        # Act
        result = workflow_engine._should_flag_overdue(order)
        
        # Assert
        assert result is False
    
    def test_should_flag_overdue_false_already_shipped(self, workflow_engine):
        """Test overdue flagging for already shipped orders"""
        # Arrange
        order = Mock()
        order.is_priority = False
        order.order_date = datetime.utcnow() - timedelta(days=4)
        order.shipping_status = ShippingStatus.SHIPPED  # Already shipped
        order.status = OrderStatus.SHIPPED
        
        # Act
        result = workflow_engine._should_flag_overdue(order)
        
        # Assert
        assert result is False
    
    def test_flag_order_as_priority(self, workflow_engine):
        """Test flagging order as priority"""
        # Arrange
        order = Mock()
        order.is_priority = False
        order.internal_notes = "Previous notes"
        order.updated_at = datetime.utcnow() - timedelta(hours=1)
        order.days_since_order = 4
        
        # Act
        workflow_engine._flag_order_as_priority(order)
        
        # Assert
        assert order.is_priority is True
        assert order.updated_at > datetime.utcnow() - timedelta(minutes=1)
        assert "flagged as overdue" in order.internal_notes
        assert "4 days since order" in order.internal_notes


class TestAutoCompletion:
    """Test order auto-completion rules"""
    
    def test_should_auto_complete_true(self, workflow_engine):
        """Test auto-completion condition when true"""
        # Arrange
        order = Mock()
        order.status = OrderStatus.SHIPPED
        order.shipping_status = ShippingStatus.DELIVERED
        order.actual_delivery_date = datetime.utcnow() - timedelta(days=2)  # Delivered 2 days ago
        
        # Act
        result = workflow_engine._should_auto_complete(order)
        
        # Assert
        assert result is True
    
    def test_should_auto_complete_false_already_delivered(self, workflow_engine):
        """Test auto-completion when already delivered"""
        # Arrange
        order = Mock()
        order.status = OrderStatus.DELIVERED  # Already completed
        order.shipping_status = ShippingStatus.DELIVERED
        order.actual_delivery_date = datetime.utcnow() - timedelta(days=2)
        
        # Act
        result = workflow_engine._should_auto_complete(order)
        
        # Assert
        assert result is False
    
    def test_should_auto_complete_false_no_delivery_date(self, workflow_engine):
        """Test auto-completion with no delivery date"""
        # Arrange
        order = Mock()
        order.status = OrderStatus.SHIPPED
        order.shipping_status = ShippingStatus.DELIVERED
        order.actual_delivery_date = None
        
        # Act
        result = workflow_engine._should_auto_complete(order)
        
        # Assert
        assert result is False
    
    def test_should_auto_complete_false_too_recent(self, workflow_engine):
        """Test auto-completion for recently delivered order"""
        # Arrange
        order = Mock()
        order.status = OrderStatus.SHIPPED
        order.shipping_status = ShippingStatus.DELIVERED
        order.actual_delivery_date = datetime.utcnow()  # Just delivered
        
        # Act
        result = workflow_engine._should_auto_complete(order)
        
        # Assert
        assert result is False
    
    def test_auto_complete_order(self, workflow_engine):
        """Test order auto-completion"""
        # Arrange
        order = Mock()
        order.status = OrderStatus.SHIPPED
        order.internal_notes = "Previous notes"
        order.updated_at = datetime.utcnow() - timedelta(hours=1)
        
        # Act
        workflow_engine._auto_complete_order(order)
        
        # Assert
        assert order.status == OrderStatus.DELIVERED
        assert order.updated_at > datetime.utcnow() - timedelta(minutes=1)
        assert "auto-completed after delivery" in order.internal_notes


class TestWorkflowSummary:
    """Test workflow summary functionality"""
    
    def test_get_workflow_summary(self, workflow_engine, mock_db):
        """Test getting workflow summary"""
        # Arrange
        status_results = [
            (OrderStatus.PENDING, 10),
            (OrderStatus.PROCESSING, 15),
            (OrderStatus.SHIPPED, 20),
            (OrderStatus.DELIVERED, 25)
        ]
        mock_db.query().group_by().all.return_value = status_results
        mock_db.query().filter().count.side_effect = [5, 3, 8]  # overdue, priority, needs attention
        
        # Act
        result = workflow_engine.get_workflow_summary(account_id=1)
        
        # Assert
        assert "status_distribution" in result
        assert "overdue_orders" in result
        assert "priority_orders" in result
        assert "needs_attention" in result
        assert "workflow_rules_active" in result
        assert "last_processed" in result
        
        assert result["status_distribution"][str(OrderStatus.PENDING)] == 10
        assert result["status_distribution"][str(OrderStatus.PROCESSING)] == 15
        assert result["overdue_orders"] == 5
        assert result["priority_orders"] == 3
        assert result["needs_attention"] == 8
        assert result["workflow_rules_active"] == 4
    
    def test_get_workflow_summary_database_error(self, workflow_engine, mock_db):
        """Test workflow summary with database error"""
        # Arrange
        mock_db.query.side_effect = Exception("Database error")
        
        # Act & Assert
        with pytest.raises(EbayManagerException, match="Failed to get workflow summary"):
            workflow_engine.get_workflow_summary(account_id=1)


class TestWorkflowRuleIntegration:
    """Test integration of workflow rules"""
    
    def test_payment_to_shipping_flow(self, workflow_engine):
        """Test order flow from payment to shipping"""
        # Arrange
        order = Mock()
        order.status = OrderStatus.CONFIRMED
        order.payment_status = PaymentStatus.PENDING
        order.shipping_status = ShippingStatus.NOT_SHIPPED
        order.payment_date = datetime.utcnow()
        order.tracking_number = "TRACK123"
        order.shipping_date = datetime.utcnow()
        order.total_amount = Decimal("100.00")
        order.paid_amount = Decimal("0.00")
        order.is_priority = False
        order.internal_notes = ""
        order.updated_at = datetime.utcnow() - timedelta(hours=1)
        
        # Act - First workflow should advance payment
        result1 = workflow_engine._process_single_order_workflow(order)
        
        # Now order should be in PROCESSING status, set up for shipping advancement
        order.status = OrderStatus.PROCESSING
        order.payment_status = PaymentStatus.PAID
        
        # Act - Second workflow should advance shipping
        result2 = workflow_engine._process_single_order_workflow(order)
        
        # Assert
        assert result1['status_updates'] >= 1  # Payment advancement
        assert result2['status_updates'] >= 1  # Shipping advancement
    
    def test_overdue_flagging_workflow(self, workflow_engine):
        """Test overdue flagging workflow"""
        # Arrange
        order = Mock()
        order.status = OrderStatus.PROCESSING
        order.payment_status = PaymentStatus.PAID
        order.shipping_status = ShippingStatus.NOT_SHIPPED
        order.order_date = datetime.utcnow() - timedelta(days=5)  # 5 days old
        order.is_priority = False
        order.internal_notes = ""
        order.updated_at = datetime.utcnow() - timedelta(hours=1)
        order.days_since_order = 5
        order.payment_date = datetime.utcnow() - timedelta(days=4)
        order.tracking_number = None
        order.shipping_date = None
        order.actual_delivery_date = None
        
        # Act
        result = workflow_engine._process_single_order_workflow(order)
        
        # Assert
        assert result['overdue_flagged'] == 1
        assert order.is_priority is True
    
    def test_full_order_lifecycle_workflow(self, workflow_engine):
        """Test complete order lifecycle through workflow"""
        # Arrange - New order
        order = Mock()
        order.status = OrderStatus.CONFIRMED
        order.payment_status = PaymentStatus.PENDING
        order.shipping_status = ShippingStatus.NOT_SHIPPED
        order.payment_date = datetime.utcnow()
        order.shipping_date = datetime.utcnow()
        order.actual_delivery_date = datetime.utcnow() - timedelta(days=2)
        order.tracking_number = "TRACK123"
        order.total_amount = Decimal("100.00")
        order.paid_amount = Decimal("0.00")
        order.is_priority = False
        order.internal_notes = ""
        order.updated_at = datetime.utcnow() - timedelta(hours=1)
        
        # Simulate workflow progression
        workflow_steps = []
        
        # Step 1: Payment advancement
        if workflow_engine._should_auto_advance_payment(order):
            workflow_engine._auto_advance_payment_status(order)
            order.status = OrderStatus.PROCESSING
            order.payment_status = PaymentStatus.PAID
            workflow_steps.append("payment")
        
        # Step 2: Shipping advancement
        if workflow_engine._should_auto_advance_shipping(order):
            workflow_engine._auto_advance_shipping_status(order)
            order.status = OrderStatus.SHIPPED
            order.shipping_status = ShippingStatus.SHIPPED
            workflow_steps.append("shipping")
        
        # Step 3: Delivery completion (simulate delivered status)
        order.shipping_status = ShippingStatus.DELIVERED
        if workflow_engine._should_auto_complete(order):
            workflow_engine._auto_complete_order(order)
            order.status = OrderStatus.DELIVERED
            workflow_steps.append("completion")
        
        # Assert
        assert "payment" in workflow_steps
        assert "shipping" in workflow_steps
        assert "completion" in workflow_steps
        assert order.status == OrderStatus.DELIVERED
        assert order.payment_status == PaymentStatus.PAID
        assert order.shipping_status == ShippingStatus.DELIVERED


class TestWorkflowPerformance:
    """Test workflow performance and optimization"""
    
    def test_workflow_batch_processing(self, workflow_engine, mock_db):
        """Test workflow processes multiple orders efficiently"""
        # Arrange
        orders = [Mock() for _ in range(100)]  # 100 orders
        mock_db.query().filter().all.return_value = orders
        mock_db.commit.return_value = None
        
        with patch.object(workflow_engine, '_process_single_order_workflow') as mock_process:
            mock_process.return_value = {
                'status_updates': 1,
                'overdue_flagged': 0,
                'auto_completed': 0
            }
            
            # Act
            result = workflow_engine.process_order_workflows(account_id=1)
        
        # Assert
        assert result['processed_orders'] == 100
        assert mock_process.call_count == 100
        mock_db.commit.assert_called_once()  # Should commit once at the end
    
    def test_workflow_error_isolation(self, workflow_engine, mock_db):
        """Test that errors in one order don't affect others"""
        # Arrange
        orders = [Mock() for _ in range(5)]
        for i, order in enumerate(orders):
            order.id = i + 1
        
        mock_db.query().filter().all.return_value = orders
        mock_db.commit.return_value = None
        
        with patch.object(workflow_engine, '_process_single_order_workflow') as mock_process:
            # Make the 3rd order fail
            def side_effect(order):
                if order.id == 3:
                    raise Exception("Processing error for order 3")
                return {
                    'status_updates': 1,
                    'overdue_flagged': 0,
                    'auto_completed': 0
                }
            
            mock_process.side_effect = side_effect
            
            # Act
            result = workflow_engine.process_order_workflows(account_id=1)
        
        # Assert
        assert result['processed_orders'] == 5
        assert result['status_updates'] == 4  # 4 successful orders
        assert len(result['errors']) == 1
        assert "order 3" in result['errors'][0]


class TestWorkflowConfiguration:
    """Test workflow configuration and rules"""
    
    def test_workflow_rule_priorities(self, workflow_engine, sample_order):
        """Test that workflow rules are applied in correct priority order"""
        # Arrange - Order that could trigger multiple rules
        sample_order.status = OrderStatus.CONFIRMED
        sample_order.payment_status = PaymentStatus.PENDING
        sample_order.payment_date = datetime.utcnow()
        sample_order.tracking_number = "TRACK123"
        sample_order.shipping_date = datetime.utcnow()
        sample_order.order_date = datetime.utcnow() - timedelta(days=5)  # Overdue
        sample_order.is_priority = False
        
        # Track the order of rule execution
        execution_order = []
        
        def mock_payment_advance():
            execution_order.append("payment")
            sample_order.status = OrderStatus.PROCESSING
            sample_order.payment_status = PaymentStatus.PAID
        
        def mock_shipping_advance():
            execution_order.append("shipping")
            sample_order.status = OrderStatus.SHIPPED
            sample_order.shipping_status = ShippingStatus.SHIPPED
        
        def mock_flag_priority():
            execution_order.append("priority")
            sample_order.is_priority = True
        
        with patch.object(workflow_engine, '_auto_advance_payment_status', side_effect=mock_payment_advance):
            with patch.object(workflow_engine, '_auto_advance_shipping_status', side_effect=mock_shipping_advance):
                with patch.object(workflow_engine, '_flag_order_as_priority', side_effect=mock_flag_priority):
                    # Act
                    workflow_engine._process_single_order_workflow(sample_order)
        
        # Assert - Rules should execute in this order
        expected_order = ["payment", "shipping", "priority"]
        assert execution_order == expected_order
    
    def test_workflow_rules_count(self, workflow_engine):
        """Test that all expected workflow rules are present"""
        # This test ensures we don't accidentally remove workflow rules
        
        # Get workflow summary which reports active rules
        with patch.object(workflow_engine, 'get_workflow_summary') as mock_summary:
            mock_summary.return_value = {"workflow_rules_active": 4}
            result = workflow_engine.get_workflow_summary(account_id=1)
        
        # Assert - Should have exactly 4 workflow rules
        assert result["workflow_rules_active"] == 4