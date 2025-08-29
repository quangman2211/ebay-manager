"""
Unit tests for Order Analytics Service
Following SOLID principles for analytics testing
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session

from app.services.order_analytics import OrderAnalyticsService
from app.models.order import Order, OrderStatus, PaymentStatus, ShippingStatus
from app.models.user import User
from app.core.exceptions import EbayManagerException


class TestOrderAnalyticsService:
    """Test Order Analytics Service following SOLID principles"""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        return Mock(spec=Session)
    
    @pytest.fixture
    def analytics_service(self, mock_db):
        """Create OrderAnalyticsService instance with mocked dependencies"""
        return OrderAnalyticsService(mock_db)
    
    @pytest.fixture
    def sample_orders(self):
        """Sample orders for testing"""
        base_date = datetime.utcnow() - timedelta(days=15)
        orders = []
        
        for i in range(10):
            order = Mock()
            order.id = i + 1
            order.account_id = 1
            order.user_id = 1
            order.total_amount = Decimal("100.00")
            order.status = OrderStatus.COMPLETED
            order.payment_status = PaymentStatus.PAID
            order.shipping_status = ShippingStatus.DELIVERED
            order.order_date = base_date + timedelta(days=i)
            order.shipping_date = base_date + timedelta(days=i + 1)
            order.tracking_number = f"TRACK{i+1:03d}"
            orders.append(order)
        
        return orders


class TestDashboardStatistics:
    """Test dashboard statistics functionality"""
    
    def test_get_dashboard_stats_success(self, analytics_service, mock_db, sample_orders):
        """Test successful dashboard statistics retrieval"""
        # Arrange
        mock_user = Mock()
        mock_user.id = 1
        mock_user.role = "user"
        mock_db.query().filter().first.return_value = mock_user
        
        # Mock order queries
        mock_query = Mock()
        mock_query.count.return_value = 10
        mock_query.with_entities().scalar.return_value = Decimal("1000.00")
        mock_db.query().filter.return_value = mock_query
        
        with patch.object(analytics_service, '_get_status_distribution', return_value={"completed": 8, "pending": 2}):
            with patch.object(analytics_service, '_get_recent_trends', return_value={"order_change_percentage": 5.0}):
                with patch.object(analytics_service, '_get_performance_metrics', return_value={"tracking_rate_percentage": 90.0}):
                    with patch.object(analytics_service, '_get_order_alerts', return_value=[]):
                        # Act
                        result = analytics_service.get_dashboard_stats(
                            account_id=1,
                            user_id=1,
                            date_range=30
                        )
        
        # Assert
        assert "total_orders" in result
        assert "total_revenue" in result
        assert "average_order_value" in result
        assert "status_distribution" in result
        assert "trends" in result
        assert "performance_metrics" in result
        assert "alerts" in result
        
        assert result["total_orders"] == 10
        assert result["total_revenue"] == 1000.00
        assert result["average_order_value"] == 100.00
    
    def test_get_dashboard_stats_no_orders(self, analytics_service, mock_db):
        """Test dashboard statistics with no orders"""
        # Arrange
        mock_user = Mock()
        mock_user.role = "user"
        mock_db.query().filter().first.return_value = mock_user
        
        mock_query = Mock()
        mock_query.count.return_value = 0
        mock_query.with_entities().scalar.return_value = None
        mock_db.query().filter.return_value = mock_query
        
        with patch.object(analytics_service, '_get_status_distribution', return_value={}):
            with patch.object(analytics_service, '_get_recent_trends', return_value={"order_change_percentage": 0}):
                with patch.object(analytics_service, '_get_performance_metrics', return_value={"tracking_rate_percentage": 0}):
                    with patch.object(analytics_service, '_get_order_alerts', return_value=[]):
                        # Act
                        result = analytics_service.get_dashboard_stats(
                            account_id=1,
                            user_id=1,
                            date_range=30
                        )
        
        # Assert
        assert result["total_orders"] == 0
        assert result["total_revenue"] == 0.0
        assert result["average_order_value"] == 0
    
    def test_get_dashboard_stats_invalid_user(self, analytics_service, mock_db):
        """Test dashboard statistics with invalid user"""
        # Arrange
        mock_db.query().filter().first.return_value = None
        
        # Act & Assert
        with pytest.raises(EbayManagerException, match="User not found"):
            analytics_service.get_dashboard_stats(
                account_id=1,
                user_id=999,
                date_range=30
            )


class TestRevenueAnalysis:
    """Test revenue analysis functionality"""
    
    def test_get_revenue_analysis_monthly(self, analytics_service, mock_db):
        """Test monthly revenue analysis"""
        # Arrange
        mock_user = Mock()
        mock_user.role = "user"
        mock_db.query().filter().first.return_value = mock_user
        
        revenue_data = [
            {"period": "2023-01", "orders": 50, "revenue": 5000.0},
            {"period": "2023-02", "orders": 75, "revenue": 7500.0},
            {"period": "2023-03", "orders": 60, "revenue": 6000.0}
        ]
        
        with patch.object(analytics_service, '_get_revenue_by_period', return_value=revenue_data):
            with patch.object(analytics_service, '_calculate_revenue_growth', return_value={"growth_rate": 20.0, "trend": "growth"}):
                with patch.object(analytics_service, '_get_revenue_by_payment_status', return_value={"paid": 18500.0}):
                    # Act
                    result = analytics_service.get_revenue_analysis(
                        account_id=1,
                        user_id=1,
                        period="monthly"
                    )
        
        # Assert
        assert "period" in result
        assert "revenue_timeline" in result
        assert "growth_analysis" in result
        assert "revenue_by_payment_status" in result
        assert "total_revenue" in result
        assert "total_orders" in result
        
        assert result["period"] == "monthly"
        assert result["total_revenue"] == 18500.0
        assert result["total_orders"] == 185
        assert len(result["revenue_timeline"]) == 3
    
    def test_get_revenue_analysis_weekly(self, analytics_service, mock_db):
        """Test weekly revenue analysis"""
        # Arrange
        mock_user = Mock()
        mock_user.role = "user"
        mock_db.query().filter().first.return_value = mock_user
        
        with patch.object(analytics_service, '_get_revenue_by_period', return_value=[]):
            with patch.object(analytics_service, '_calculate_revenue_growth', return_value={"growth_rate": 0.0, "trend": "stable"}):
                with patch.object(analytics_service, '_get_revenue_by_payment_status', return_value={}):
                    # Act
                    result = analytics_service.get_revenue_analysis(
                        account_id=1,
                        user_id=1,
                        period="weekly"
                    )
        
        # Assert
        assert result["period"] == "weekly"
        assert isinstance(result["revenue_timeline"], list)
    
    def test_get_revenue_analysis_invalid_period(self, analytics_service, mock_db):
        """Test revenue analysis with invalid period"""
        # Arrange
        mock_user = Mock()
        mock_user.role = "user"
        mock_db.query().filter().first.return_value = mock_user
        
        # Act & Assert
        with pytest.raises(ValueError, match="Invalid period"):
            analytics_service.get_revenue_analysis(
                account_id=1,
                user_id=1,
                period="invalid"
            )


class TestPerformanceReports:
    """Test performance reporting functionality"""
    
    def test_get_order_performance_report_success(self, analytics_service, mock_db):
        """Test successful performance report generation"""
        # Arrange
        mock_user = Mock()
        mock_user.role = "user"
        mock_db.query().filter().first.return_value = mock_user
        
        with patch.object(analytics_service, '_get_average_processing_time', return_value=24.5):
            with patch.object(analytics_service, '_get_fulfillment_rate', return_value=95.0):
                with patch.object(analytics_service, '_get_on_time_shipping_rate', return_value=88.0):
                    with patch.object(analytics_service, '_get_overdue_orders_analysis', return_value={"count": 5, "oldest_days": 7}):
                        with patch.object(analytics_service, '_identify_problem_areas', return_value=["low_tracking_rate"]):
                            # Act
                            result = analytics_service.get_order_performance_report(
                                account_id=1,
                                user_id=1
                            )
        
        # Assert
        assert "analysis_period" in result
        assert "average_processing_time_hours" in result
        assert "fulfillment_rate_percentage" in result
        assert "on_time_shipping_percentage" in result
        assert "overdue_orders" in result
        assert "problem_areas" in result
        assert "recommendations" in result
        
        assert result["average_processing_time_hours"] == 24.5
        assert result["fulfillment_rate_percentage"] == 95.0
        assert result["on_time_shipping_percentage"] == 88.0
        assert len(result["problem_areas"]) == 1
    
    def test_get_performance_metrics_with_tracking(self, analytics_service, mock_db):
        """Test performance metrics calculation with tracking data"""
        # Arrange
        mock_db.query().filter().count.side_effect = [80, 100]  # 80 with tracking, 100 total
        
        # Act
        result = analytics_service._get_performance_metrics(
            account_id=1,
            date_range=30
        )
        
        # Assert
        assert result["tracking_rate_percentage"] == 80.0
        assert result["orders_with_tracking"] == 80
        assert result["total_orders_analyzed"] == 100
    
    def test_get_performance_metrics_no_orders(self, analytics_service, mock_db):
        """Test performance metrics with no orders"""
        # Arrange
        mock_db.query().filter().count.return_value = 0
        
        # Act
        result = analytics_service._get_performance_metrics(
            account_id=1,
            date_range=30
        )
        
        # Assert
        assert result["tracking_rate_percentage"] == 0
        assert result["orders_with_tracking"] == 0
        assert result["total_orders_analyzed"] == 0


class TestStatusDistribution:
    """Test order status distribution analysis"""
    
    def test_get_status_distribution(self, analytics_service, mock_db):
        """Test getting order status distribution"""
        # Arrange
        mock_query = Mock()
        mock_results = [
            (OrderStatus.PENDING, 10),
            (OrderStatus.CONFIRMED, 25),
            (OrderStatus.SHIPPED, 40),
            (OrderStatus.DELIVERED, 25)
        ]
        mock_query.with_entities().group_by().all.return_value = mock_results
        
        # Act
        result = analytics_service._get_status_distribution(mock_query)
        
        # Assert
        assert len(result) == 4
        assert result[str(OrderStatus.PENDING)] == 10
        assert result[str(OrderStatus.CONFIRMED)] == 25
        assert result[str(OrderStatus.SHIPPED)] == 40
        assert result[str(OrderStatus.DELIVERED)] == 25
    
    def test_get_status_distribution_empty(self, analytics_service, mock_db):
        """Test status distribution with no orders"""
        # Arrange
        mock_query = Mock()
        mock_query.with_entities().group_by().all.return_value = []
        
        # Act
        result = analytics_service._get_status_distribution(mock_query)
        
        # Assert
        assert result == {}


class TestRecentTrends:
    """Test recent trends analysis"""
    
    def test_get_recent_trends_growth(self, analytics_service, mock_db):
        """Test recent trends showing growth"""
        # Arrange
        current_week_result = Mock()
        current_week_result.orders = 50
        current_week_result.revenue = Decimal("5000.00")
        
        previous_week_result = Mock()
        previous_week_result.orders = 40
        previous_week_result.revenue = Decimal("4000.00")
        
        mock_db.query().filter.side_effect = [
            Mock(first=Mock(return_value=current_week_result)),
            Mock(first=Mock(return_value=previous_week_result))
        ]
        
        # Act
        result = analytics_service._get_recent_trends(account_id=1)
        
        # Assert
        assert result["current_week_orders"] == 50
        assert result["current_week_revenue"] == 5000.0
        assert result["previous_week_orders"] == 40
        assert result["previous_week_revenue"] == 4000.0
        assert result["order_change_percentage"] == 25.0  # (50-40)/40 * 100
        assert result["revenue_change_percentage"] == 25.0
    
    def test_get_recent_trends_decline(self, analytics_service, mock_db):
        """Test recent trends showing decline"""
        # Arrange
        current_week_result = Mock()
        current_week_result.orders = 30
        current_week_result.revenue = Decimal("3000.00")
        
        previous_week_result = Mock()
        previous_week_result.orders = 40
        previous_week_result.revenue = Decimal("4000.00")
        
        mock_db.query().filter.side_effect = [
            Mock(first=Mock(return_value=current_week_result)),
            Mock(first=Mock(return_value=previous_week_result))
        ]
        
        # Act
        result = analytics_service._get_recent_trends(account_id=1)
        
        # Assert
        assert result["order_change_percentage"] == -25.0  # (30-40)/40 * 100
        assert result["revenue_change_percentage"] == -25.0
    
    def test_get_recent_trends_no_previous_data(self, analytics_service, mock_db):
        """Test recent trends with no previous data"""
        # Arrange
        current_week_result = Mock()
        current_week_result.orders = 50
        current_week_result.revenue = Decimal("5000.00")
        
        previous_week_result = Mock()
        previous_week_result.orders = 0
        previous_week_result.revenue = None
        
        mock_db.query().filter.side_effect = [
            Mock(first=Mock(return_value=current_week_result)),
            Mock(first=Mock(return_value=previous_week_result))
        ]
        
        # Act
        result = analytics_service._get_recent_trends(account_id=1)
        
        # Assert
        assert result["order_change_percentage"] == 0
        assert result["revenue_change_percentage"] == 0


class TestOrderAlerts:
    """Test order alerts functionality"""
    
    def test_get_order_alerts_overdue_orders(self, analytics_service, mock_db):
        """Test alerts for overdue orders"""
        # Arrange
        mock_db.query().filter().count.side_effect = [5, 2]  # 5 overdue, 2 pending payment
        
        # Act
        result = analytics_service._get_order_alerts(account_id=1)
        
        # Assert
        assert len(result) == 2
        
        overdue_alert = next(alert for alert in result if alert["type"] == "overdue_orders")
        assert overdue_alert["severity"] == "high"
        assert overdue_alert["count"] == 5
        assert "overdue for shipping" in overdue_alert["message"]
        
        pending_alert = next(alert for alert in result if alert["type"] == "pending_payment")
        assert pending_alert["severity"] == "medium"
        assert pending_alert["count"] == 2
    
    def test_get_order_alerts_no_issues(self, analytics_service, mock_db):
        """Test alerts when no issues exist"""
        # Arrange
        mock_db.query().filter().count.return_value = 0
        
        # Act
        result = analytics_service._get_order_alerts(account_id=1)
        
        # Assert
        assert result == []


class TestRevenueCalculations:
    """Test revenue calculation methods"""
    
    def test_calculate_revenue_growth_positive(self, analytics_service):
        """Test positive revenue growth calculation"""
        # Arrange
        revenue_data = [
            {"revenue": 1000.0},
            {"revenue": 1200.0},
            {"revenue": 1500.0}
        ]
        
        # Act
        result = analytics_service._calculate_revenue_growth(revenue_data)
        
        # Assert
        assert result["growth_rate"] == 50.0  # (1500-1000)/1000 * 100
        assert result["trend"] == "strong_growth"
    
    def test_calculate_revenue_growth_negative(self, analytics_service):
        """Test negative revenue growth calculation"""
        # Arrange
        revenue_data = [
            {"revenue": 1500.0},
            {"revenue": 1200.0},
            {"revenue": 1000.0}
        ]
        
        # Act
        result = analytics_service._calculate_revenue_growth(revenue_data)
        
        # Assert
        assert result["growth_rate"] == -33.33  # (1000-1500)/1500 * 100
        assert result["trend"] == "decline"
    
    def test_calculate_revenue_growth_insufficient_data(self, analytics_service):
        """Test revenue growth with insufficient data"""
        # Arrange
        revenue_data = [{"revenue": 1000.0}]  # Only one data point
        
        # Act
        result = analytics_service._calculate_revenue_growth(revenue_data)
        
        # Assert
        assert result["growth_rate"] == 0.0
        assert result["trend"] == "insufficient_data"
    
    def test_get_revenue_by_payment_status(self, analytics_service, mock_db):
        """Test revenue breakdown by payment status"""
        # Arrange
        mock_results = [
            (PaymentStatus.PAID, Decimal("15000.00")),
            (PaymentStatus.PENDING, Decimal("2500.00")),
            (PaymentStatus.FAILED, Decimal("500.00"))
        ]
        mock_db.query().filter().group_by().all.return_value = mock_results
        
        # Act
        result = analytics_service._get_revenue_by_payment_status(
            account_id=1,
            start_date=datetime.utcnow() - timedelta(days=30),
            end_date=datetime.utcnow()
        )
        
        # Assert
        assert result[str(PaymentStatus.PAID)] == 15000.0
        assert result[str(PaymentStatus.PENDING)] == 2500.0
        assert result[str(PaymentStatus.FAILED)] == 500.0


class TestPerformanceMetrics:
    """Test performance metric calculations"""
    
    def test_get_average_processing_time(self, analytics_service, mock_db):
        """Test average processing time calculation"""
        # Arrange
        mock_orders = []
        for i in range(5):
            order = Mock()
            order.order_date = datetime.utcnow() - timedelta(days=5-i, hours=12)
            order.shipping_date = datetime.utcnow() - timedelta(days=5-i)  # 12 hours later
            mock_orders.append(order)
        
        mock_db.query().filter().all.return_value = mock_orders
        
        # Act
        result = analytics_service._get_average_processing_time(
            account_id=1,
            start_date=datetime.utcnow() - timedelta(days=30),
            end_date=datetime.utcnow()
        )
        
        # Assert
        assert result == 12.0  # 12 hours average
    
    def test_get_fulfillment_rate(self, analytics_service, mock_db):
        """Test fulfillment rate calculation"""
        # Arrange
        mock_db.query().filter().count.side_effect = [100, 85]  # 100 total, 85 fulfilled
        
        # Act
        result = analytics_service._get_fulfillment_rate(
            account_id=1,
            start_date=datetime.utcnow() - timedelta(days=30),
            end_date=datetime.utcnow()
        )
        
        # Assert
        assert result == 85.0
    
    def test_get_on_time_shipping_rate(self, analytics_service, mock_db):
        """Test on-time shipping rate calculation"""
        # Arrange
        mock_orders = []
        for i in range(10):
            order = Mock()
            order.order_date = datetime.utcnow() - timedelta(days=10-i)
            # 7 orders shipped within 3 days, 3 orders shipped later
            if i < 7:
                order.shipping_date = order.order_date + timedelta(days=2)  # On time
            else:
                order.shipping_date = order.order_date + timedelta(days=5)  # Late
            mock_orders.append(order)
        
        mock_db.query().filter().all.return_value = mock_orders
        
        # Act
        result = analytics_service._get_on_time_shipping_rate(
            account_id=1,
            start_date=datetime.utcnow() - timedelta(days=30),
            end_date=datetime.utcnow()
        )
        
        # Assert
        assert result == 70.0  # 7 out of 10 orders on time


class TestProblemAreaIdentification:
    """Test problem area identification"""
    
    def test_identify_problem_areas_multiple_issues(self, analytics_service, mock_db):
        """Test identification of multiple problem areas"""
        # Arrange
        # Mock high overdue rate (20%)
        mock_db.query().filter().count.side_effect = [100, 20, 25]  # total, overdue, pending payment
        
        with patch.object(analytics_service, '_get_performance_metrics', return_value={"tracking_rate_percentage": 70.0}):
            # Act
            result = analytics_service._identify_problem_areas(
                account_id=1,
                start_date=datetime.utcnow() - timedelta(days=30),
                end_date=datetime.utcnow()
            )
        
        # Assert
        assert "high_overdue_rate" in result
        assert "low_tracking_rate" in result
        assert "high_pending_payment_rate" in result
    
    def test_identify_problem_areas_no_issues(self, analytics_service, mock_db):
        """Test identification when no problems exist"""
        # Arrange
        mock_db.query().filter().count.side_effect = [100, 5, 10]  # total, overdue (5%), pending (10%)
        
        with patch.object(analytics_service, '_get_performance_metrics', return_value={"tracking_rate_percentage": 90.0}):
            # Act
            result = analytics_service._identify_problem_areas(
                account_id=1,
                start_date=datetime.utcnow() - timedelta(days=30),
                end_date=datetime.utcnow()
            )
        
        # Assert
        assert result == []


class TestRecommendations:
    """Test performance recommendations"""
    
    def test_generate_performance_recommendations_multiple_issues(self, analytics_service):
        """Test recommendations for multiple performance issues"""
        # Act
        result = analytics_service._generate_performance_recommendations(
            avg_processing_time=120.0,  # 5 days - too long
            fulfillment_rate=85.0,      # Below 90% - needs improvement
            on_time_shipping=80.0       # Below 85% - needs improvement
        )
        
        # Assert
        assert len(result) == 3
        assert any("processing time" in rec for rec in result)
        assert any("fulfillment rate" in rec for rec in result)
        assert any("shipping timeliness" in rec for rec in result)
    
    def test_generate_performance_recommendations_good_performance(self, analytics_service):
        """Test recommendations for good performance"""
        # Act
        result = analytics_service._generate_performance_recommendations(
            avg_processing_time=24.0,   # 1 day - good
            fulfillment_rate=95.0,      # Above 90% - good
            on_time_shipping=90.0       # Above 85% - good
        )
        
        # Assert
        assert len(result) == 1
        assert "maintain current processes" in result[0].lower()


class TestErrorHandling:
    """Test error handling in analytics service"""
    
    def test_dashboard_stats_database_error(self, analytics_service, mock_db):
        """Test handling of database errors in dashboard stats"""
        # Arrange
        mock_db.query.side_effect = Exception("Database connection error")
        
        # Act & Assert
        with pytest.raises(EbayManagerException, match="Failed to get dashboard stats"):
            analytics_service.get_dashboard_stats(
                account_id=1,
                user_id=1,
                date_range=30
            )
    
    def test_revenue_analysis_database_error(self, analytics_service, mock_db):
        """Test handling of database errors in revenue analysis"""
        # Arrange
        mock_user = Mock()
        mock_user.role = "user"
        mock_db.query().filter().first.return_value = mock_user
        mock_db.query.side_effect = [Mock(), Exception("Database error")]
        
        # Act & Assert
        with pytest.raises(EbayManagerException, match="Failed to get revenue analysis"):
            analytics_service.get_revenue_analysis(
                account_id=1,
                user_id=1,
                period="monthly"
            )