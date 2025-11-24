# Product Importer Application

Web application for importing products from CSV files (up to 500,000 records) with real-time progress tracking, product management, and webhook support.

## Features

- CSV import with real-time progress tracking (SSE)
- Product CRUD with filtering and pagination
- Bulk delete operations
- Webhook configuration and management

## Tech Stack

- FastAPI, Celery, Redis, SQLAlchemy, PostgreSQL

## Quick Start

1. Install dependencies: `pip install -r requirements.txt`
2. Set environment variables: `cp .env.example .env`
3. Start Redis: `redis-server`
4. Start Celery worker: `celery -A app.tasks.celery_app worker --loglevel=info`
5. Start application: `uvicorn app.main:app --reload`

## CSV Format

Required columns: `sku`, `name` (case-insensitive). Optional: `description`

```csv
sku,name,description
SKU-001,Product 1,Description 1
```

## API Endpoints

- Products: `GET/POST/PUT/DELETE /api/products`, `DELETE /api/products/bulk/all`
- Upload: `POST /api/upload`, `GET /api/progress/{task_id}`, `GET /api/stream/{task_id}`
- Webhooks: `GET/POST/PUT/DELETE /api/webhooks`, `POST /api/webhooks/{id}/test`

## Deployment

### Render.com / Heroku

1. Set environment variables: `DATABASE_URL`, `REDIS_URL`, `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`, `SECRET_KEY`
2. Deploy web service with start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
3. Deploy background worker: `celery -A app.tasks.celery_app worker --loglevel=info`

## Performance

- Chunked processing (1000 products per batch)
- Bulk database operations with case-insensitive SKU matching
- Connection pooling and async task processing

