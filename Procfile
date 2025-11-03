web: gunicorn artscope.wsgi:application --bind 0.0.0.0:$PORT
worker: celery -A artscope worker --loglevel=info
