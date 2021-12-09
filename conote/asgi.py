"""
ASGI entrypoint. Configures Django and then runs the application
defined in the ASGI_APPLICATION setting.
"""

import os
import django
from channels.routing import get_default_application
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "conf.settings")
django.setup()
application = get_default_application()
