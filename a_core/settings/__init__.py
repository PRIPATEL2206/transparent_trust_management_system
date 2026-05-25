import os
from pathlib import Path

# Load .env file if python-dotenv is available
try:
    from dotenv import load_dotenv
    _env_file = Path(__file__).resolve().parent.parent.parent / '.env'
    if _env_file.exists():
        load_dotenv(_env_file)
except ImportError:
    pass

environment = os.environ.get('DJANGO_ENV', 'development')

if environment == 'production':
    from .production import *  # noqa: F401,F403
elif environment == 'test':
    from .test import *  # noqa: F401,F403
else:
    from .development import *  # noqa: F401,F403
