from . import checks  # noqa: F401 - registers system checks


def _on_ready():
    """Runs once after Django is fully initialized."""
    import os
    if os.environ.get('RUN_MAIN') == 'true' or os.environ.get('DJANGO_ENV') == 'production':
        from services.shutdown import register_shutdown_handlers
        register_shutdown_handlers()

        from services.startup import run_startup_validation
        run_startup_validation()


_on_ready()