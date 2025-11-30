#!/bin/bash
# Start both web server and Celery worker in the same process

# Start Celery worker in the background
celery -A app.tasks.celery_app.celery_app worker --loglevel=info --concurrency=2 &
CELERY_PID=$!

# Start web server in the foreground
uvicorn app.main:app --host 0.0.0.0 --port $PORT

# If web server exits, kill Celery worker
kill $CELERY_PID 2>/dev/null
