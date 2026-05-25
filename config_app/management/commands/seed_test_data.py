"""
Seeds the database with realistic test data for manual UI testing.

Usage:
    python manage.py seed_test_data
    python manage.py seed_test_data --cleanup
"""

import uuid
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone


TEST_PASSWORD = 'Test@12345'

TEST_USERS = [
    {'username': 'manager1', 'email': 'manager1@test.local', 'role': 'admin', 'first_name': 'Rajesh', 'last_name': 'Kumar'},
    {'username': 'member1', 'email': 'member1@test.local', 'role': 'member', 'first_name': 'Priya', 'last_name': 'Sharma'},
    {'username': 'member2', 'email': 'member2@test.local', 'role': 'member', 'first_name': 'Ankit', 'last_name': 'Patel'},
    {'username': 'user1', 'email': 'user1@test.local', 'role': 'user', 'first_name': 'Sneha', 'last_name': 'Gupta'},
    {'username': 'ngo_org1', 'email': 'ngo@helpinghands.local', 'role': 'ngo', 'first_name': 'Helping', 'last_name': 'Hands NGO'},
]

DONATION_TYPES = [
    {'name': 'General Fund', 'desc': 'Contributions towards the general operating fund of the trust'},
    {'name': 'Education Fund', 'desc': 'Support for educational programs and scholarships'},
    {'name': 'Medical Aid', 'desc': 'Donations for medical assistance to needy families'},
    {'name': 'Infrastructure', 'desc': 'Building and maintenance of community infrastructure'},
]

EXPENSE_CATEGORIES = [
    {'name': 'Office Supplies', 'description': 'Stationery, printing, office consumables'},
    {'name': 'Travel', 'description': 'Travel and transportation expenses'},
    {'name': 'Events', 'description': 'Event organization and venue costs'},
    {'name': 'Maintenance', 'description': 'Building and equipment maintenance'},
    {'name': 'Utilities', 'description': 'Electricity, water, internet bills'},
]

PRODUCT_CATEGORIES = [
    {'name': 'Books', 'description': 'Educational books and publications'},
    {'name': 'Merchandise', 'description': 'Trust branded merchandise'},
    {'name': 'Stationery', 'description': 'Writing and office materials'},
]

PRODUCTS = [
    {'name': 'Trust Annual Report 2024', 'description': 'Detailed annual report of trust activities and financial summary.', 'price': '150.00', 'stock': 100, 'category': 'Books', 'discount_percent': '0'},
    {'name': 'Trust T-Shirt (Unisex)', 'description': 'Comfortable cotton t-shirt with trust logo. Available in all sizes.', 'price': '499.00', 'stock': 50, 'category': 'Merchandise', 'discount_percent': '10'},
    {'name': 'Scholarship Application Kit', 'description': 'Complete kit with forms, guidelines, and checklist for scholarship applicants.', 'price': '50.00', 'stock': 200, 'category': 'Stationery', 'discount_percent': '0'},
    {'name': 'Community Cookbook', 'description': 'Recipes collected from trust community members. All proceeds go to the general fund.', 'price': '250.00', 'stock': 75, 'category': 'Books', 'discount_percent': '15'},
    {'name': 'Trust Coffee Mug', 'description': 'Ceramic mug with inspirational quote and trust branding.', 'price': '199.00', 'stock': 150, 'category': 'Merchandise', 'discount_percent': '5'},
]

NOTICES = [
    {'title': 'Annual General Meeting', 'content': 'The AGM will be held on June 15th at the Community Hall. All members are required to attend. Agenda includes election of new committee members and financial report presentation.', 'priority': 'high'},
    {'title': 'Office Hours Change', 'content': 'Effective next month, office hours will be 9 AM to 5 PM on weekdays. Saturday hours remain 10 AM to 2 PM.', 'priority': 'medium'},
    {'title': 'New Scholarship Program', 'content': 'We are launching a new scholarship program for underprivileged students. Applications open from July 1st. Eligible candidates must have scored above 75% in their last examination.', 'priority': 'medium'},
    {'title': 'Maintenance Work Notice', 'content': 'The community hall will be closed for renovation from June 20-25. Please plan events accordingly.', 'priority': 'low'},
]

DONATIONS = [
    {'display_name': 'Ramesh Agarwal', 'amount': 25000, 'handover_by': 'Cash at office', 'desc': 'Annual contribution', 'is_approved': True},
    {'display_name': 'Meena Foundation', 'amount': 100000, 'handover_by': 'Bank transfer', 'desc': 'CSR grant for education', 'is_approved': True},
    {'display_name': 'Anonymous Donor', 'amount': 5000, 'handover_by': 'Online payment', 'desc': 'Monthly donation', 'is_approved': True},
    {'display_name': 'Patel Family Trust', 'amount': 50000, 'handover_by': 'Cheque', 'desc': 'Medical aid fund', 'is_approved': False},
    {'display_name': 'Suresh Reddy', 'amount': 10000, 'handover_by': 'UPI', 'desc': 'Infrastructure development', 'is_approved': False},
]

EXPENSES = [
    {'title': 'Printer Paper (500 sheets x 10)', 'amount': '2500.00', 'description': 'Monthly stationery stock for office', 'category': 'Office Supplies', 'status': 'paid'},
    {'title': 'Community Hall Electricity Bill', 'amount': '8500.00', 'description': 'Quarterly electricity bill for community hall', 'category': 'Utilities', 'status': 'approved'},
    {'title': 'Annual Day Event Venue', 'amount': '35000.00', 'description': 'Venue booking for annual trust celebration event', 'category': 'Events', 'status': 'pending'},
    {'title': 'Plumbing Repair', 'amount': '4200.00', 'description': 'Emergency plumbing repair in community kitchen', 'category': 'Maintenance', 'status': 'draft'},
    {'title': 'Committee Travel to District Office', 'amount': '3800.00', 'description': 'Travel for document verification at district office', 'category': 'Travel', 'status': 'pending'},
]

NGO_REQUESTS = [
    {'title': 'School Supplies for 50 Children', 'description': 'We need funds to provide school bags, notebooks, and stationery to 50 underprivileged children in our area for the upcoming academic year.', 'amount_requested': '75000.00', 'status': 'pending'},
    {'title': 'Medical Camp Organization', 'description': 'Request for funds to organize a free medical camp in rural area. Includes doctor fees, medicines, and transport.', 'amount_requested': '120000.00', 'status': 'under_review'},
]


class Command(BaseCommand):
    help = 'Seed database with realistic test data for manual testing'

    def add_arguments(self, parser):
        parser.add_argument('--cleanup', action='store_true', help='Remove all test data')

    def handle(self, *args, **options):
        if options['cleanup']:
            self._cleanup()
        else:
            self._seed()

    def _seed(self):
        self.stdout.write('Seeding test data...\n')

        users = self._create_users()
        admin_user = User.objects.filter(username='admin').first()
        if not admin_user:
            self.stdout.write(self.style.WARNING('No admin user found. Run setup_project --create-admin first.'))
            return

        donation_types = self._create_donation_types(admin_user)
        expense_categories = self._create_expense_categories()
        product_categories = self._create_product_categories()
        self._create_products(product_categories)
        self._create_donations(users, donation_types)
        self._create_expenses(users, expense_categories, admin_user)
        self._create_notices(users, admin_user)
        self._create_ngo_requests(users)
        self._create_transactions(users)

        self.stdout.write(self.style.SUCCESS('\nTest data seeded successfully!'))
        self.stdout.write('\nTest accounts (password for all: Test@12345):')
        self.stdout.write('  admin     → super_admin (already exists)')
        self.stdout.write('  manager1  → admin role')
        self.stdout.write('  member1   → member role')
        self.stdout.write('  member2   → member role')
        self.stdout.write('  user1     → user role')
        self.stdout.write('  ngo_org1  → ngo role')

    def _create_users(self):
        from roles.services import RoleService

        users = {}
        for u in TEST_USERS:
            user, created = User.objects.get_or_create(
                username=u['username'],
                defaults={
                    'email': u['email'],
                    'first_name': u['first_name'],
                    'last_name': u['last_name'],
                }
            )
            if created:
                user.set_password(TEST_PASSWORD)
                user.save()
                RoleService.assign_role(user, u['role'])
                self.stdout.write(f'  Created user: {u["username"]} ({u["role"]})')
            else:
                self.stdout.write(f'  Already exists: {u["username"]}')
            users[u['username']] = user

        return users

    def _create_donation_types(self, admin_user):
        from donations.models import DonationType

        types = {}
        for dt in DONATION_TYPES:
            obj, created = DonationType.objects.get_or_create(
                name=dt['name'],
                defaults={'desc': dt['desc'], 'created_by': admin_user, 'is_forever': True}
            )
            types[dt['name']] = obj
            if created:
                self.stdout.write(f'  Created donation type: {dt["name"]}')

        return types

    def _create_expense_categories(self):
        from expenses.models import ExpenseCategory

        categories = {}
        for ec in EXPENSE_CATEGORIES:
            obj, created = ExpenseCategory.objects.get_or_create(
                name=ec['name'],
                defaults={'description': ec['description']}
            )
            categories[ec['name']] = obj
            if created:
                self.stdout.write(f'  Created expense category: {ec["name"]}')

        return categories

    def _create_product_categories(self):
        from products.models import ProductCategory

        categories = {}
        for pc in PRODUCT_CATEGORIES:
            obj, created = ProductCategory.objects.get_or_create(
                name=pc['name'],
                defaults={'description': pc['description']}
            )
            categories[pc['name']] = obj
            if created:
                self.stdout.write(f'  Created product category: {pc["name"]}')

        return categories

    def _create_products(self, categories):
        from products.models import Product

        for p in PRODUCTS:
            _, created = Product.objects.get_or_create(
                name=p['name'],
                defaults={
                    'description': p['description'],
                    'price': Decimal(p['price']),
                    'stock': p['stock'],
                    'discount_percent': Decimal(p['discount_percent']),
                    'category': categories.get(p['category']),
                    'is_active': True,
                }
            )
            if created:
                self.stdout.write(f'  Created product: {p["name"]}')

    def _create_donations(self, users, donation_types):
        from donations.models import Donation

        member = users.get('member1')
        if not member:
            return

        type_list = list(donation_types.values())
        for i, d in enumerate(DONATIONS):
            dtype = type_list[i % len(type_list)]
            _, created = Donation.objects.get_or_create(
                display_name=d['display_name'],
                donation_for=dtype,
                defaults={
                    'add_by': member,
                    'amount': d['amount'],
                    'handover_by': d['handover_by'],
                    'desc': d['desc'],
                    'is_approved': d['is_approved'],
                }
            )
            if created:
                self.stdout.write(f'  Created donation: {d["display_name"]} - ₹{d["amount"]}')

    def _create_expenses(self, users, categories, admin_user):
        from expenses.models import Expense

        member = users.get('member1')
        if not member:
            return

        for e in EXPENSES:
            cat = categories.get(e['category'])
            defaults = {
                'raised_by': member,
                'description': e['description'],
                'amount': Decimal(e['amount']),
                'category': cat,
                'status': e['status'],
            }
            if e['status'] in ('approved', 'paid'):
                defaults['approved_by'] = admin_user
                defaults['approved_at'] = timezone.now() - timedelta(days=2)

            _, created = Expense.objects.get_or_create(
                title=e['title'],
                defaults=defaults
            )
            if created:
                self.stdout.write(f'  Created expense: {e["title"]} ({e["status"]})')

    def _create_notices(self, users, admin_user):
        from notices.models import Notice

        for n in NOTICES:
            _, created = Notice.objects.get_or_create(
                title=n['title'],
                defaults={
                    'content': n['content'],
                    'created_by': admin_user,
                    'is_approved': True,
                    'priority': n['priority'],
                    'expires_at': timezone.now() + timedelta(days=30),
                }
            )
            if created:
                self.stdout.write(f'  Created notice: {n["title"]}')

    def _create_ngo_requests(self, users):
        from ngo_requests.models import FundRequest

        ngo_user = users.get('ngo_org1')
        if not ngo_user:
            return

        for r in NGO_REQUESTS:
            _, created = FundRequest.objects.get_or_create(
                title=r['title'],
                ngo_user=ngo_user,
                defaults={
                    'description': r['description'],
                    'amount_requested': Decimal(r['amount_requested']),
                    'status': r['status'],
                }
            )
            if created:
                self.stdout.write(f'  Created NGO request: {r["title"]}')

    def _create_transactions(self, users):
        from payments.models import Transaction

        member = users.get('member1')
        if not member:
            return

        transactions = [
            {'type': 'membership', 'amount': '1000.00', 'status': 'completed'},
            {'type': 'donation', 'amount': '5000.00', 'status': 'completed'},
            {'type': 'fee', 'amount': '200.00', 'status': 'completed'},
        ]

        for t in transactions:
            _, created = Transaction.objects.get_or_create(
                user=member,
                transaction_type=t['type'],
                amount=Decimal(t['amount']),
                defaults={
                    'status': t['status'],
                    'idempotency_key': str(uuid.uuid4()),
                    'completed_at': timezone.now() - timedelta(days=5) if t['status'] == 'completed' else None,
                }
            )
            if created:
                self.stdout.write(f'  Created transaction: {t["type"]} - ₹{t["amount"]}')

    def _cleanup(self):
        from donations.models import Donation, DonationType
        from expenses.models import Expense, ExpenseCategory
        from notices.models import Notice, Notification
        from products.models import Product, ProductCategory, Order
        from ngo_requests.models import FundRequest
        from payments.models import Transaction, Receipt

        usernames = [u['username'] for u in TEST_USERS]

        Donation.objects.filter(display_name__in=[d['display_name'] for d in DONATIONS]).delete()
        Expense.objects.filter(title__in=[e['title'] for e in EXPENSES]).delete()
        Notice.objects.filter(title__in=[n['title'] for n in NOTICES]).delete()
        Product.objects.filter(name__in=[p['name'] for p in PRODUCTS]).delete()
        FundRequest.objects.filter(title__in=[r['title'] for r in NGO_REQUESTS]).delete()
        Transaction.objects.filter(user__username__in=usernames).delete()
        Order.objects.filter(user__username__in=usernames).delete()
        Notification.objects.filter(recipient__username__in=usernames).delete()

        DonationType.objects.filter(name__in=[d['name'] for d in DONATION_TYPES]).delete()
        ExpenseCategory.objects.filter(name__in=[e['name'] for e in EXPENSE_CATEGORIES]).delete()
        ProductCategory.objects.filter(name__in=[p['name'] for p in PRODUCT_CATEGORIES]).delete()

        deleted, _ = User.objects.filter(username__in=usernames).delete()
        self.stdout.write(self.style.SUCCESS(f'Cleaned up {deleted} test user(s) and all associated data.'))
