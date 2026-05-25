import re

from locust import TaskSet, task


class AdminBehavior(TaskSet):
    """Simulates admin workflows: dashboard, approvals, exports, user management."""

    USERNAME = "loadtest_admin"
    PASSWORD = "LoadTest_Admin123!"

    def on_start(self):
        self._login()

    def _login(self):
        login_page = self.client.get("/auth/login/", name="Login Page (admin)")
        csrf = self._extract_csrf(login_page.text)
        self.client.post(
            "/auth/login/",
            data={
                "username": self.USERNAME,
                "password": self.PASSWORD,
                "csrfmiddlewaretoken": csrf,
            },
            headers={"Referer": self.client.base_url + "/auth/login/"},
            name="Admin Login Submit",
        )

    def _extract_csrf(self, html):
        match = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', html)
        return match.group(1) if match else ""

    @task(5)
    def view_dashboard(self):
        self.client.get("/dashboard/", name="Dashboard")

    @task(3)
    def view_dashboard_analytics(self):
        self.client.get("/dashboard/analytics/", name="Dashboard Analytics")

    @task(4)
    def view_pending_approvals(self):
        self.client.get("/approvals/", name="Approval Queue")

    @task(2)
    def view_donation_admin(self):
        self.client.get("/donations/admin/", name="Donation Admin")

    @task(2)
    def view_expenses_admin(self):
        self.client.get("/expenses/", name="Expenses Admin List")

    @task(2)
    def view_ngo_requests(self):
        self.client.get("/ngo-requests/", name="NGO Requests")

    @task(1)
    def export_donations_csv(self):
        self.client.get("/reports/export/donations/?format=csv", name="Export Donations CSV")

    @task(1)
    def export_expenses_csv(self):
        self.client.get("/reports/export/expenses/?format=csv", name="Export Expenses CSV")

    @task(3)
    def view_reports(self):
        self.client.get("/reports/", name="Reports")

    @task(2)
    def view_roles_management(self):
        self.client.get("/roles/", name="Roles Management")

    @task(1)
    def view_config(self):
        self.client.get("/config/", name="Site Config")

    @task(2)
    def view_notices_management(self):
        self.client.get("/notices/manage/", name="Notices Management")

    @task(1)
    def approve_action(self):
        page = self.client.get("/approvals/", name="Approval Queue (pre-action)")
        csrf = self._extract_csrf(page.text)
        approval_id = self._find_first_pending(page.text)
        if approval_id and csrf:
            self.client.post(
                f"/approvals/{approval_id}/approve/",
                data={"notes": "Load test approval", "csrfmiddlewaretoken": csrf},
                headers={"Referer": self.client.base_url + "/approvals/"},
                name="Approve Item",
            )

    def _find_first_pending(self, html):
        match = re.search(r'/approvals/(\d+)/approve/', html)
        return match.group(1) if match else None
