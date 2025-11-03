"""
ASGI config for artscope project.
"""
import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'artscope.settings')

application = get_asgi_application()
