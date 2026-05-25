from locust import TaskSet, task


class AnonymousBehavior(TaskSet):
    """Public page browsing — no authentication required."""

    @task(5)
    def view_home(self):
        self.client.get("/", name="Home")

    @task(3)
    def view_transparency(self):
        self.client.get("/transparency/", name="Transparency")

    @task(2)
    def view_login_page(self):
        self.client.get("/auth/login/", name="Login Page")

    @task(2)
    def view_register_page(self):
        self.client.get("/auth/register/", name="Register Page")

    @task(1)
    def view_notices_public(self):
        self.client.get("/notices/", name="Notices (Public)")

    @task(1)
    def health_check(self):
        self.client.get("/health/live/", name="Health Live")
