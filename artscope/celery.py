"""
Celery configuration for ArtScope
NOTE: Celery is DISABLED for free tier deployment (no Redis available)
Tasks will run synchronously via CELERY_TASK_ALWAYS_EAGER setting
"""
import os

# Celery is disabled - importing would fail without celery package
# from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'artscope.settings')

# app = Celery('artscope')
# app.config_from_object('django.conf:settings', namespace='CELERY')
# app.autodiscover_tasks()

# @app.task(bind=True, ignore_result=True)
# def debug_task(self):
#     print(f'Request: {self.request!r}')
