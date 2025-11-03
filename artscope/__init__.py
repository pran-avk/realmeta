"""
ArtScope Django Application
"""
default_app_config = 'artscope.apps.ArtscopeConfig'

# Ensure Celery app is loaded when Django starts
from .celery import app as celery_app

__all__ = ('celery_app',)
