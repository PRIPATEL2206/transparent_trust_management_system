from django.apps import AppConfig


class ConfigAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'config_app'
    verbose_name = 'Site Configuration'

    def ready(self):
        import config_app.signals  # noqa: F401
