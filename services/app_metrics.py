"""
Application-specific metric instrumentation.

Call these from views/services to track business events.
Metrics are exposed via the /metrics/ Prometheus endpoint.
"""
from services.metrics import increment_counter, set_gauge


def track_login_success():
    increment_counter('logins_success')


def track_login_failure():
    increment_counter('logins_failure')


def track_registration():
    increment_counter('registrations')


def track_donation_created():
    increment_counter('donations_created')


def track_donation_approved():
    increment_counter('donations_approved')


def track_expense_created():
    increment_counter('expenses_created')


def track_expense_approved():
    increment_counter('expenses_approved')


def track_payment_completed():
    increment_counter('payments_completed')


def track_payment_failed():
    increment_counter('payments_failed')


def track_2fa_verified():
    increment_counter('2fa_verifications')


def track_email_sent():
    increment_counter('emails_sent')


def update_active_users(count):
    set_gauge('active_users', count)


def update_pending_approvals(count):
    set_gauge('pending_approvals', count)
