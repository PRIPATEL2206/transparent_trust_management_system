"""
Trust Management System - Load Testing Suite

Run with:
    locust -f loadtests/locustfile.py --host=http://localhost:8000
    locust -f loadtests/locustfile.py --host=http://localhost:8000 --headless -u 50 -r 5 -t 60s

User classes weighted by realistic traffic distribution:
    - AnonymousUser (40%): browsing public pages
    - AuthenticatedUser (40%): logged-in member actions
    - AdminUser (20%): admin dashboard and approval workflows
"""

from locust import HttpUser, task, between, events
from loadtests.scenarios.anonymous import AnonymousBehavior
from loadtests.scenarios.authenticated import AuthenticatedBehavior
from loadtests.scenarios.admin import AdminBehavior


class AnonymousUser(HttpUser):
    """Simulates unauthenticated visitors browsing public pages."""
    weight = 4
    wait_time = between(2, 8)
    tasks = [AnonymousBehavior]


class AuthenticatedUser(HttpUser):
    """Simulates logged-in members performing daily operations."""
    weight = 4
    wait_time = between(1, 5)
    tasks = [AuthenticatedBehavior]


class AdminUser(HttpUser):
    """Simulates admin users managing approvals and viewing reports."""
    weight = 2
    wait_time = between(2, 6)
    tasks = [AdminBehavior]
