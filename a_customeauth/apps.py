from django.apps import AppConfig


class ACustomeauthConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'a_customeauth'

    def ready(self):
        import a_customeauth.signals
        return super().ready()