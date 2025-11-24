# Product Importer Application

A scalable web application for importing products from CSV files (up to 500,000 records) with real-time progress tracking, product management, and webhook support.

## Features

- **CSV Import**: Upload and import large CSV files (up to 500K products) with real-time progress tracking
- **Product Management**: View, create, update, and delete products with filtering and pagination
- **Bulk Operations**: Delete all products with confirmation
- **Webhook Support**: Configure and manage webhooks for product events
- **Real-time Updates**: Server-Sent Events (SSE) for live progress updates

## Tech Stack

- **Web Framework**: FastAPI
- **Task Queue**: Celery with Redis
- **ORM**: SQLAlchemy
- **Database**: PostgreSQL
- **Frontend**: Vanilla HTML/CSS/JavaScript

## Prerequisites

- Python 3.11+
- PostgreSQL
- Redis
- pip

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd product-importer
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your database and Redis URLs
```

5. Initialize the database:
```bash
# The application will create tables automatically on first run
# Or use Alembic for migrations:
# alembic upgrade head
```

## Running Locally

1. Start Redis:
```bash
redis-server
```

2. Start Celery worker (in a separate terminal):
```bash
celery -A app.tasks.celery_app worker --loglevel=info
```

3. Start the FastAPI application:
```bash
uvicorn app.main:app --reload
```

4. Open your browser and navigate to:
```
http://localhost:8000
```

## CSV Format

The CSV file should have the following columns (case-insensitive):
- `sku` (required): Unique product SKU
- `name` (required): Product name
- `description` (optional): Product description

Example:
```csv
sku,name,description
SKU-001,Product 1,Description 1
SKU-002,Product 2,Description 2
```

## API Endpoints

### Products
- `GET /api/products` - List products (with pagination and filters)
- `GET /api/products/{id}` - Get single product
- `POST /api/products` - Create product
- `PUT /api/products/{id}` - Update product
- `DELETE /api/products/{id}` - Delete product
- `DELETE /api/products/bulk/all` - Delete all products

### Upload
- `POST /api/upload` - Upload CSV file
- `GET /api/progress/{task_id}` - Get import progress (polling)
- `GET /api/stream/{task_id}` - Stream progress via SSE

### Webhooks
- `GET /api/webhooks` - List webhooks
- `GET /api/webhooks/{id}` - Get webhook
- `POST /api/webhooks` - Create webhook
- `PUT /api/webhooks/{id}` - Update webhook
- `DELETE /api/webhooks/{id}` - Delete webhook
- `POST /api/webhooks/{id}/test` - Test webhook

## Deployment

### Render.com

1. Create a new Web Service on Render
2. Connect your GitHub repository
3. Set the following environment variables:
   - `DATABASE_URL`: PostgreSQL connection string
   - `REDIS_URL`: Redis connection string
   - `CELERY_BROKER_URL`: Redis connection string (same as REDIS_URL)
   - `CELERY_RESULT_BACKEND`: Redis connection string (same as REDIS_URL)
   - `SECRET_KEY`: A secure random string
   - `ENVIRONMENT`: production

4. Set build command: `pip install -r requirements.txt`
5. Set start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

6. Create a separate Background Worker service:
   - Build command: `pip install -r requirements.txt`
   - Start command: `celery -A app.tasks.celery_app worker --loglevel=info`

### Heroku

1. Create a Heroku app:
```bash
heroku create your-app-name
```

2. Add PostgreSQL and Redis addons:
```bash
heroku addons:create heroku-postgresql:mini
heroku addons:create heroku-redis:mini
```

3. Set environment variables:
```bash
heroku config:set SECRET_KEY=your-secret-key
heroku config:set ENVIRONMENT=production
```

4. Deploy:
```bash
git push heroku main
```

5. Start worker dyno:
```bash
heroku ps:scale worker=1
```

## Project Structure

```
product-importer/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration
│   ├── database.py          # Database setup
│   ├── models.py            # SQLAlchemy models
│   ├── schemas.py           # Pydantic schemas
│   ├── api/                 # API endpoints
│   │   ├── products.py
│   │   ├── upload.py
│   │   ├── webhooks.py
│   │   └── sse.py
│   ├── services/            # Business logic
│   │   ├── csv_processor.py
│   │   ├── product_service.py
│   │   └── webhook_service.py
│   ├── tasks/               # Celery tasks
│   │   ├── celery_app.py
│   │   └── import_tasks.py
│   └── static/              # Frontend files
│       ├── index.html
│       ├── css/
│       └── js/
├── requirements.txt
├── Procfile
├── runtime.txt
└── README.md
```

## Performance Optimizations

- **Chunked Processing**: CSV files are processed in 10K row chunks
- **Bulk Upserts**: PostgreSQL `ON CONFLICT` for efficient duplicate handling
- **Case-insensitive SKU**: Unique index on `lower(sku)` for case-insensitive matching
- **Async Tasks**: Heavy operations run in Celery workers
- **Connection Pooling**: SQLAlchemy connection pool for database efficiency
- **SSE Streaming**: Real-time progress updates without polling overhead

## Notes

- The application handles large file uploads by processing them asynchronously
- Duplicate products (by SKU) are automatically overwritten
- SKU matching is case-insensitive
- Webhooks are triggered asynchronously and don't block main operations
- Progress tracking uses Redis with 1-hour TTL

## License

MIT

