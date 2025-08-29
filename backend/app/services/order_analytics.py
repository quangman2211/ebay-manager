"""
Order Analytics Service
Following YAGNI/SOLID principles - Essential analytics only
"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, extract, desc, asc

from app.models.order import Order, OrderItem, OrderStatus, PaymentStatus, ShippingStatus
from app.models.user import User
from app.core.exceptions import EbayManagerException
from app.core.logging import get_logger

logger = get_logger("order_analytics")

class OrderAnalyticsService:
    """
    Order analytics service for business insights
    Following SOLID: Single Responsibility for order analytics
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_dashboard_stats(
        self, 
        account_id: int, 
        user_id: int,
        date_range: Optional[int] = 30
    ) -> Dict[str, Any]:
        """
        Get dashboard statistics for orders
        Following YAGNI: Essential metrics only
        """
        
        try:
            # Validate access
            self._validate_account_access(account_id, user_id)
            
            # Date range for analysis
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=date_range)
            
            # Base query
            base_query = self.db.query(Order).filter(
                and_(
                    Order.account_id == account_id,
                    Order.order_date >= start_date,
                    Order.order_date <= end_date
                )
            )
            
            # Basic metrics
            total_orders = base_query.count()
            total_revenue = base_query.with_entities(
                func.sum(Order.total_amount)
            ).scalar() or Decimal('0.00')
            
            # Status distribution
            status_distribution = self._get_status_distribution(base_query)
            
            # Recent trends (last 7 days vs previous 7 days)
            trends = self._get_recent_trends(account_id)
            
            # Top performing metrics
            performance_metrics = self._get_performance_metrics(account_id, date_range)
            
            # Alerts and issues
            alerts = self._get_order_alerts(account_id)
            
            return {
                'date_range_days': date_range,
                'period_start': start_date.isoformat(),
                'period_end': end_date.isoformat(),
                'total_orders': total_orders,
                'total_revenue': float(total_revenue),
                'average_order_value': float(total_revenue / total_orders) if total_orders > 0 else 0,
                'status_distribution': status_distribution,
                'trends': trends,
                'performance_metrics': performance_metrics,
                'alerts': alerts
            }
            
        except Exception as e:
            logger.error(f"Failed to get dashboard stats: {str(e)}")
            if isinstance(e, EbayManagerException):
                raise
            raise EbayManagerException(f"Failed to get dashboard stats: {str(e)}")
    
    def get_revenue_analysis(
        self, 
        account_id: int, 
        user_id: int,
        period: str = 'monthly'
    ) -> Dict[str, Any]:
        """
        Get revenue analysis over time
        Following YAGNI: Basic revenue trends only
        """
        
        try:
            # Validate access
            self._validate_account_access(account_id, user_id)
            
            # Determine date range based on period
            if period == 'weekly':
                weeks_back = 12
                end_date = datetime.utcnow()
                start_date = end_date - timedelta(weeks=weeks_back)
                group_by_format = 'week'
            elif period == 'monthly':
                months_back = 12
                end_date = datetime.utcnow()
                start_date = end_date - timedelta(days=months_back * 30)
                group_by_format = 'month'
            else:
                raise ValueError(f"Invalid period: {period}")
            
            # Revenue by time period
            revenue_data = self._get_revenue_by_period(account_id, start_date, end_date, group_by_format)
            
            # Calculate growth rates
            growth_analysis = self._calculate_revenue_growth(revenue_data)
            
            # Revenue by payment status
            payment_status_revenue = self._get_revenue_by_payment_status(account_id, start_date, end_date)
            
            return {
                'period': period,
                'period_start': start_date.isoformat(),
                'period_end': end_date.isoformat(),
                'revenue_timeline': revenue_data,
                'growth_analysis': growth_analysis,
                'revenue_by_payment_status': payment_status_revenue,
                'total_revenue': sum(item['revenue'] for item in revenue_data),
                'total_orders': sum(item['orders'] for item in revenue_data)
            }
            
        except Exception as e:
            logger.error(f"Failed to get revenue analysis: {str(e)}")
            if isinstance(e, EbayManagerException):
                raise
            raise EbayManagerException(f"Failed to get revenue analysis: {str(e)}")
    
    def get_order_performance_report(
        self, 
        account_id: int, 
        user_id: int
    ) -> Dict[str, Any]:
        """
        Get order processing performance report
        Following YAGNI: Essential performance metrics only
        """
        
        try:
            # Validate access
            self._validate_account_access(account_id, user_id)
            
            # Last 30 days
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=30)
            
            # Performance metrics
            avg_processing_time = self._get_average_processing_time(account_id, start_date, end_date)
            fulfillment_rate = self._get_fulfillment_rate(account_id, start_date, end_date)
            on_time_shipping = self._get_on_time_shipping_rate(account_id, start_date, end_date)
            
            # Issue analysis
            overdue_orders = self._get_overdue_orders_analysis(account_id)
            problem_areas = self._identify_problem_areas(account_id, start_date, end_date)
            
            return {
                'analysis_period': '30_days',
                'period_start': start_date.isoformat(),
                'period_end': end_date.isoformat(),
                'average_processing_time_hours': avg_processing_time,
                'fulfillment_rate_percentage': fulfillment_rate,
                'on_time_shipping_percentage': on_time_shipping,
                'overdue_orders': overdue_orders,
                'problem_areas': problem_areas,
                'recommendations': self._generate_performance_recommendations(
                    avg_processing_time, fulfillment_rate, on_time_shipping
                )
            }
            
        except Exception as e:
            logger.error(f"Failed to get performance report: {str(e)}")
            if isinstance(e, EbayManagerException):
                raise
            raise EbayManagerException(f"Failed to get performance report: {str(e)}")
    
    def _validate_account_access(self, account_id: int, user_id: int):
        """Validate user access to account"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise EbayManagerException("User not found", error_code="USER_NOT_FOUND")
        
        if user.role != 'admin':
            # Check if user owns the account (simplified - should use proper account relationship)
            pass  # For now, allow access (should be properly implemented)
    
    def _get_status_distribution(self, base_query) -> Dict[str, int]:
        """Get distribution of orders by status"""
        
        results = base_query.with_entities(
            Order.status,
            func.count(Order.id).label('count')
        ).group_by(Order.status).all()
        
        return {str(status): count for status, count in results}
    
    def _get_recent_trends(self, account_id: int) -> Dict[str, Any]:
        """Get recent trends (last 7 days vs previous 7 days)"""
        
        now = datetime.utcnow()
        
        # Current week
        current_week_start = now - timedelta(days=7)
        current_week = self.db.query(
            func.count(Order.id).label('orders'),
            func.sum(Order.total_amount).label('revenue')
        ).filter(
            and_(
                Order.account_id == account_id,
                Order.order_date >= current_week_start,
                Order.order_date <= now
            )
        ).first()
        
        # Previous week
        previous_week_start = now - timedelta(days=14)
        previous_week_end = now - timedelta(days=7)
        previous_week = self.db.query(
            func.count(Order.id).label('orders'),
            func.sum(Order.total_amount).label('revenue')
        ).filter(
            and_(
                Order.account_id == account_id,
                Order.order_date >= previous_week_start,
                Order.order_date < previous_week_end
            )
        ).first()
        
        # Calculate changes
        order_change = 0
        revenue_change = 0
        
        if previous_week.orders and previous_week.orders > 0:
            order_change = ((current_week.orders or 0) - previous_week.orders) / previous_week.orders * 100
        
        if previous_week.revenue and previous_week.revenue > 0:
            revenue_change = ((current_week.revenue or 0) - previous_week.revenue) / float(previous_week.revenue) * 100
        
        return {
            'current_week_orders': current_week.orders or 0,
            'current_week_revenue': float(current_week.revenue or 0),
            'previous_week_orders': previous_week.orders or 0,
            'previous_week_revenue': float(previous_week.revenue or 0),
            'order_change_percentage': round(order_change, 2),
            'revenue_change_percentage': round(revenue_change, 2)
        }
    
    def _get_performance_metrics(self, account_id: int, date_range: int) -> Dict[str, Any]:
        """Get performance metrics"""
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=date_range)
        
        # Orders with tracking
        orders_with_tracking = self.db.query(Order).filter(
            and_(
                Order.account_id == account_id,
                Order.order_date >= start_date,
                Order.tracking_number.isnot(None)
            )
        ).count()
        
        total_orders = self.db.query(Order).filter(
            and_(
                Order.account_id == account_id,
                Order.order_date >= start_date
            )
        ).count()
        
        tracking_rate = (orders_with_tracking / total_orders * 100) if total_orders > 0 else 0
        
        return {
            'tracking_rate_percentage': round(tracking_rate, 1),
            'orders_with_tracking': orders_with_tracking,
            'total_orders_analyzed': total_orders
        }
    
    def _get_order_alerts(self, account_id: int) -> List[Dict[str, Any]]:
        """Get order alerts and issues"""
        
        alerts = []
        
        # Overdue orders
        cutoff_date = datetime.utcnow() - timedelta(days=3)
        overdue_count = self.db.query(Order).filter(
            and_(
                Order.account_id == account_id,
                Order.order_date <= cutoff_date,
                Order.shipping_status == ShippingStatus.NOT_SHIPPED,
                Order.status.notin_([OrderStatus.CANCELLED, OrderStatus.DELIVERED])
            )
        ).count()
        
        if overdue_count > 0:
            alerts.append({
                'type': 'overdue_orders',
                'severity': 'high',
                'count': overdue_count,
                'message': f'{overdue_count} orders are overdue for shipping'
            })
        
        # Pending payment orders older than 24 hours
        payment_cutoff = datetime.utcnow() - timedelta(hours=24)
        pending_payment_count = self.db.query(Order).filter(
            and_(
                Order.account_id == account_id,
                Order.order_date <= payment_cutoff,
                Order.payment_status == PaymentStatus.PENDING,
                Order.status != OrderStatus.CANCELLED
            )
        ).count()
        
        if pending_payment_count > 0:
            alerts.append({
                'type': 'pending_payment',
                'severity': 'medium',
                'count': pending_payment_count,
                'message': f'{pending_payment_count} orders have pending payment for over 24 hours'
            })
        
        return alerts
    
    def _get_revenue_by_period(
        self, 
        account_id: int, 
        start_date: datetime, 
        end_date: datetime, 
        period: str
    ) -> List[Dict[str, Any]]:
        """Get revenue grouped by time period"""
        
        if period == 'week':
            # Group by week
            results = self.db.query(
                extract('year', Order.order_date).label('year'),
                extract('week', Order.order_date).label('week'),
                func.count(Order.id).label('orders'),
                func.sum(Order.total_amount).label('revenue')
            ).filter(
                and_(
                    Order.account_id == account_id,
                    Order.order_date >= start_date,
                    Order.order_date <= end_date
                )
            ).group_by('year', 'week').order_by('year', 'week').all()
            
            return [
                {
                    'period': f"{int(r.year)}-W{int(r.week):02d}",
                    'year': int(r.year),
                    'week': int(r.week),
                    'orders': r.orders,
                    'revenue': float(r.revenue or 0)
                }
                for r in results
            ]
        
        else:  # monthly
            results = self.db.query(
                extract('year', Order.order_date).label('year'),
                extract('month', Order.order_date).label('month'),
                func.count(Order.id).label('orders'),
                func.sum(Order.total_amount).label('revenue')
            ).filter(
                and_(
                    Order.account_id == account_id,
                    Order.order_date >= start_date,
                    Order.order_date <= end_date
                )
            ).group_by('year', 'month').order_by('year', 'month').all()
            
            return [
                {
                    'period': f"{int(r.year)}-{int(r.month):02d}",
                    'year': int(r.year),
                    'month': int(r.month),
                    'orders': r.orders,
                    'revenue': float(r.revenue or 0)
                }
                for r in results
            ]
    
    def _calculate_revenue_growth(self, revenue_data: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate revenue growth rates"""
        
        if len(revenue_data) < 2:
            return {'growth_rate': 0.0, 'trend': 'insufficient_data'}
        
        # Simple growth rate calculation (last vs first period)
        first_revenue = revenue_data[0]['revenue']
        last_revenue = revenue_data[-1]['revenue']
        
        if first_revenue > 0:
            growth_rate = ((last_revenue - first_revenue) / first_revenue) * 100
        else:
            growth_rate = 0.0
        
        # Determine trend
        if growth_rate > 10:
            trend = 'strong_growth'
        elif growth_rate > 0:
            trend = 'growth'
        elif growth_rate > -10:
            trend = 'stable'
        else:
            trend = 'decline'
        
        return {
            'growth_rate': round(growth_rate, 2),
            'trend': trend
        }
    
    def _get_revenue_by_payment_status(
        self, 
        account_id: int, 
        start_date: datetime, 
        end_date: datetime
    ) -> Dict[str, float]:
        """Get revenue breakdown by payment status"""
        
        results = self.db.query(
            Order.payment_status,
            func.sum(Order.total_amount).label('revenue')
        ).filter(
            and_(
                Order.account_id == account_id,
                Order.order_date >= start_date,
                Order.order_date <= end_date
            )
        ).group_by(Order.payment_status).all()
        
        return {str(status): float(revenue or 0) for status, revenue in results}
    
    def _get_average_processing_time(
        self, 
        account_id: int, 
        start_date: datetime, 
        end_date: datetime
    ) -> float:
        """Calculate average order processing time in hours"""
        
        # Orders with both order date and shipping date
        orders = self.db.query(Order).filter(
            and_(
                Order.account_id == account_id,
                Order.order_date >= start_date,
                Order.order_date <= end_date,
                Order.shipping_date.isnot(None)
            )
        ).all()
        
        if not orders:
            return 0.0
        
        total_hours = 0
        count = 0
        
        for order in orders:
            if order.order_date and order.shipping_date:
                processing_time = order.shipping_date - order.order_date
                total_hours += processing_time.total_seconds() / 3600
                count += 1
        
        return round(total_hours / count, 1) if count > 0 else 0.0
    
    def _get_fulfillment_rate(
        self, 
        account_id: int, 
        start_date: datetime, 
        end_date: datetime
    ) -> float:
        """Calculate order fulfillment rate"""
        
        total_orders = self.db.query(Order).filter(
            and_(
                Order.account_id == account_id,
                Order.order_date >= start_date,
                Order.order_date <= end_date,
                Order.status != OrderStatus.CANCELLED
            )
        ).count()
        
        fulfilled_orders = self.db.query(Order).filter(
            and_(
                Order.account_id == account_id,
                Order.order_date >= start_date,
                Order.order_date <= end_date,
                Order.status.in_([OrderStatus.SHIPPED, OrderStatus.DELIVERED])
            )
        ).count()
        
        return round((fulfilled_orders / total_orders * 100), 1) if total_orders > 0 else 0.0
    
    def _get_on_time_shipping_rate(
        self, 
        account_id: int, 
        start_date: datetime, 
        end_date: datetime
    ) -> float:
        """Calculate on-time shipping rate (within 3 business days)"""
        
        shipped_orders = self.db.query(Order).filter(
            and_(
                Order.account_id == account_id,
                Order.order_date >= start_date,
                Order.order_date <= end_date,
                Order.shipping_date.isnot(None)
            )
        ).all()
        
        if not shipped_orders:
            return 0.0
        
        on_time_count = 0
        
        for order in shipped_orders:
            if order.order_date and order.shipping_date:
                days_to_ship = (order.shipping_date - order.order_date).days
                if days_to_ship <= 3:  # 3 business days
                    on_time_count += 1
        
        return round((on_time_count / len(shipped_orders) * 100), 1)
    
    def _get_overdue_orders_analysis(self, account_id: int) -> Dict[str, Any]:
        """Analyze overdue orders"""
        
        cutoff_date = datetime.utcnow() - timedelta(days=3)
        
        overdue_orders = self.db.query(Order).filter(
            and_(
                Order.account_id == account_id,
                Order.order_date <= cutoff_date,
                Order.shipping_status == ShippingStatus.NOT_SHIPPED,
                Order.status.notin_([OrderStatus.CANCELLED, OrderStatus.DELIVERED])
            )
        ).all()
        
        if not overdue_orders:
            return {'count': 0, 'oldest_days': 0, 'total_value': 0}
        
        oldest_order = min(overdue_orders, key=lambda x: x.order_date)
        oldest_days = (datetime.utcnow() - oldest_order.order_date).days
        total_value = sum(float(order.total_amount) for order in overdue_orders)
        
        return {
            'count': len(overdue_orders),
            'oldest_days': oldest_days,
            'total_value': total_value
        }
    
    def _identify_problem_areas(
        self, 
        account_id: int, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[str]:
        """Identify problem areas in order processing"""
        
        problems = []
        
        # High percentage of overdue orders
        total_orders = self.db.query(Order).filter(
            and_(
                Order.account_id == account_id,
                Order.order_date >= start_date,
                Order.order_date <= end_date
            )
        ).count()
        
        overdue_orders = self.db.query(Order).filter(
            and_(
                Order.account_id == account_id,
                Order.order_date >= start_date,
                Order.order_date <= end_date - timedelta(days=3),
                Order.shipping_status == ShippingStatus.NOT_SHIPPED,
                Order.status.notin_([OrderStatus.CANCELLED, OrderStatus.DELIVERED])
            )
        ).count()
        
        if total_orders > 0 and (overdue_orders / total_orders) > 0.1:  # More than 10%
            problems.append("high_overdue_rate")
        
        # Low tracking rate
        tracking_rate = self._get_performance_metrics(account_id, 30)['tracking_rate_percentage']
        if tracking_rate < 80:
            problems.append("low_tracking_rate")
        
        # High pending payment rate
        pending_payment = self.db.query(Order).filter(
            and_(
                Order.account_id == account_id,
                Order.order_date >= start_date,
                Order.payment_status == PaymentStatus.PENDING,
                Order.status != OrderStatus.CANCELLED
            )
        ).count()
        
        if total_orders > 0 and (pending_payment / total_orders) > 0.2:  # More than 20%
            problems.append("high_pending_payment_rate")
        
        return problems
    
    def _generate_performance_recommendations(
        self, 
        avg_processing_time: float, 
        fulfillment_rate: float, 
        on_time_shipping: float
    ) -> List[str]:
        """Generate performance improvement recommendations"""
        
        recommendations = []
        
        if avg_processing_time > 72:  # More than 3 days
            recommendations.append("Reduce order processing time - consider automation or workflow optimization")
        
        if fulfillment_rate < 90:
            recommendations.append("Improve fulfillment rate - review order processing bottlenecks")
        
        if on_time_shipping < 85:
            recommendations.append("Improve shipping timeliness - consider faster shipping methods or better inventory management")
        
        if not recommendations:
            recommendations.append("Performance metrics are good - maintain current processes")
        
        return recommendations

def get_order_analytics_service(db: Session) -> OrderAnalyticsService:
    """Dependency injection for order analytics service"""
    return OrderAnalyticsService(db)