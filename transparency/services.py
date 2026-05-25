from django.db.models import Sum, Count, Q
from django.db.models.functions import TruncMonth
from django.utils import timezone
from datetime import timedelta

from services.base import BaseService


class TransparencyService(BaseService):

    @staticmethod
    def get_donation_summary():
        from donations.models import Donation, DonationType
        summary = {
            'total_amount': Donation.objects.filter(is_approved=True).aggregate(total=Sum('amount'))['total'] or 0,
            'total_count': Donation.objects.filter(is_approved=True).count(),
            'by_type': list(
                DonationType.objects.annotate(
                    total_donations=Count('donations', filter=Q(donations__is_approved=True)),
                    total_amount=Sum('donations__amount', filter=Q(donations__is_approved=True))
                ).values('name', 'total_donations', 'total_amount')
            ),
        }
        return summary

    @staticmethod
    def get_expense_summary():
        from expenses.models import Expense
        summary = {
            'total_approved': Expense.objects.filter(
                status__in=['approved', 'paid']
            ).aggregate(total=Sum('amount'))['total'] or 0,
            'total_paid': Expense.objects.filter(
                status='paid'
            ).aggregate(total=Sum('amount'))['total'] or 0,
        }
        return summary

    @staticmethod
    def get_fund_flow():
        from donations.models import Donation
        from expenses.models import Expense
        from payments.models import Transaction

        total_in = (
            (Donation.objects.filter(is_approved=True).aggregate(t=Sum('amount'))['t'] or 0) +
            (Transaction.objects.filter(status='completed').aggregate(t=Sum('amount'))['t'] or 0)
        )
        total_out = Expense.objects.filter(
            status='paid'
        ).aggregate(t=Sum('amount'))['t'] or 0

        return {
            'total_incoming': total_in,
            'total_outgoing': total_out,
            'balance': total_in - total_out,
        }

    @staticmethod
    def get_ngo_funding_summary():
        from ngo_requests.models import FundRequest
        return {
            'total_disbursed': FundRequest.objects.filter(
                status='disbursed'
            ).aggregate(total=Sum('amount_approved'))['total'] or 0,
            'total_requests': FundRequest.objects.count(),
        }

    @staticmethod
    def get_monthly_breakdown():
        from donations.models import Donation
        from expenses.models import Expense

        six_months_ago = timezone.now() - timedelta(days=180)

        monthly_donations = list(
            Donation.objects.filter(is_approved=True, created_at__gte=six_months_ago)
            .annotate(month=TruncMonth('created_at'))
            .values('month')
            .annotate(total=Sum('amount'), count=Count('id'))
            .order_by('month')
        )

        monthly_expenses = list(
            Expense.objects.filter(status='paid', created_at__gte=six_months_ago)
            .annotate(month=TruncMonth('created_at'))
            .values('month')
            .annotate(total=Sum('amount'), count=Count('id'))
            .order_by('month')
        )

        return {
            'donations': monthly_donations,
            'expenses': monthly_expenses,
        }

    @staticmethod
    def get_recent_approved_donations(limit=10):
        from donations.models import Donation
        return Donation.objects.filter(
            is_approved=True
        ).select_related('donation_for').order_by('-created_at')[:limit]
