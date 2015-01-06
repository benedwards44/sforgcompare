web: gunicorn sforgcompare.wsgi --workers $WEB_CONCURRENCY
worker: celery -A compareorgs.tasks worker -B --loglevel=info