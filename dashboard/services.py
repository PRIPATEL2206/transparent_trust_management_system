from django.db.models import Sum, Count, Q
from django.utils import timezone
from django.contrib.auth.models import User
from datetime import timedelta

from services.base import BaseService


class ActivityLogService(BaseService):

    @staticmethod
    def log(user, action, category='system', target_user=None, details=None, request=None):
        from .models import ActivityLog
        ip_address = None
        log_details = details or {}
        if request:
            ip_address = request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip()
            if not ip_address:
                ip_address = request.META.get('REMOTE_ADDR')
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            if user_agent:
                log_details['user_agent'] = user_agent[:200]

        ActivityLog.objects.create(
            user=user if user and user.is_authenticated else None,
            action=action,
            category=category,
            target_user=target_user,
            details=log_details,
            ip_address=ip_address,
        )

    @staticmethod
    def get_recent(limit=20):
        from .models import ActivityLog
        return ActivityLog.objects.select_related('user', 'target_user').order_by('-created_at')[:limit]

    @staticmethod
    def get_user_activity(user, limit=20):
        from .models import ActivityLog
        return ActivityLog.objects.filter(user=user).select_related('target_user').order_by('-created_at')[:limit]


class DashboardService(BaseService):

    @staticmethod
    def get_donation_stats():
        from django.core.cache import cache
        cache_key = 'dashboard_donation_stats'
        stats = cache.get(cache_key)
        if stats is None:
            from donations.models import Donation
            total = Donation.objects.filter(is_approved=True).aggregate(
                total_amount=Sum('amount'),
                total_count=Count('id')
            )
            pending_count = Donation.objects.filter(is_approved=False).count()
            total['pending_count'] = pending_count
            stats = total
            cache.set(cache_key, stats, 60)
        return stats

    @staticmethod
    def get_expense_stats():
        from django.core.cache import cache
        cache_key = 'dashboard_expense_stats'
        stats = cache.get(cache_key)
        if stats is None:
            from expenses.models import Expense
            stats = Expense.objects.aggregate(
                total_amount=Sum('amount'),
                total_count=Count('id'),
                pending_count=Count('id', filter=Q(status='pending')),
                approved_amount=Sum('amount', filter=Q(status='approved')),
                paid_amount=Sum('amount', filter=Q(status='paid')),
            )
            cache.set(cache_key, stats, 60)
        return stats

    @staticmethod
    def get_transaction_stats():
        from django.core.cache import cache
        cache_key = 'dashboard_transaction_stats'
        stats = cache.get(cache_key)
        if stats is None:
            from payments.models import Transaction
            stats = Transaction.objects.aggregate(
                total_amount=Sum('amount', filter=Q(status='completed')),
                total_count=Count('id', filter=Q(status='completed')),
            )
            cache.set(cache_key, stats, 60)
        return stats

    @staticmethod
    def get_user_stats():
        stats = {
            'total_users': User.objects.count(),
            'new_this_month': User.objects.filter(
                date_joined__gte=timezone.now() - timedelta(days=30)
            ).count(),
        }
        return stats

    @staticmethod
    def get_recent_activity(limit=10):
        from donations.models import Donation
        from expenses.models import Expense
        from payments.models import Transaction

        recent_donations = list(Donation.objects.select_related('add_by').order_by('-created_at')[:5])
        recent_expenses = list(Expense.objects.select_related('raised_by').order_by('-created_at')[:5])
        recent_transactions = list(Transaction.objects.select_related('user').order_by('-created_at')[:5])

        return {
            'donations': recent_donations,
            'expenses': recent_expenses,
            'transactions': recent_transactions,
        }

    @staticmethod
    def get_monthly_summary():
        from donations.models import Donation
        from payments.models import Transaction

        now = timezone.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        donations_this_month = Donation.objects.filter(
            created_at__gte=month_start,
            is_approved=True
        ).aggregate(total=Sum('amount'))['total'] or 0

        payments_this_month = Transaction.objects.filter(
            created_at__gte=month_start,
            status='completed'
        ).aggregate(total=Sum('amount'))['total'] or 0

        return {
            'donations_this_month': donations_this_month,
            'payments_this_month': payments_this_month,
        }
