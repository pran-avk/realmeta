"""
Celery Periodic Tasks Configuration
"""
from celery import Celery
from celery.schedules import crontab

app = Celery('artscope')


app.conf.beat_schedule = {
    # Clean up old sessions daily at 2 AM
    'cleanup-old-sessions': {
        'task': 'embeddings.tasks.cleanup_old_sessions',
        'schedule': crontab(hour=2, minute=0),
    },
    
    # Aggregate analytics daily at 3 AM
    'aggregate-analytics': {
        'task': 'embeddings.tasks.aggregate_analytics',
        'schedule': crontab(hour=3, minute=0),
    },
    
    # Update artwork counters every hour
    'update-artwork-counters': {
        'task': 'embeddings.tasks.update_artwork_counters',
        'schedule': crontab(minute=0),  # Every hour
    },
    
    # Process visitor feedback every 30 minutes
    'process-feedback': {
        'task': 'embeddings.tasks.process_visitor_feedback',
        'schedule': crontab(minute='*/30'),
    },
}

app.conf.timezone = 'UTC'
