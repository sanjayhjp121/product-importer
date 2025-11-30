# Render Quick Start Checklist

## Quick Deployment Steps

### 1. Create Database (PostgreSQL)
- [ ] Go to Render Dashboard → New → PostgreSQL
- [ ] Name: `product-importer-db`
- [ ] Copy **Internal Database URL**

### 2. Create Redis
- [ ] Go to Render Dashboard → New → Redis  
- [ ] Name: `product-importer-redis`
- [ ] Copy **Internal Redis URL**

### 3. Deploy Web Service
- [ ] Go to Render Dashboard → New → Web Service
- [ ] Connect your Git repository
- [ ] Build Command: `pip install -r requirements.txt`
- [ ] Start Command: `python init_db.py && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- [ ] Add Environment Variables:
  - [ ] `DATABASE_URL` = (Internal Database URL)
  - [ ] `REDIS_URL` = (Internal Redis URL)
  - [ ] `CELERY_BROKER_URL` = (same as REDIS_URL)
  - [ ] `CELERY_RESULT_BACKEND` = (same as REDIS_URL)
  - [ ] `SECRET_KEY` = (generate: `openssl rand -hex 32`)
  - [ ] `DEBUG` = `false`
  - [ ] `ENVIRONMENT` = `production`

### 4. Deploy Worker Service
- [ ] Go to Render Dashboard → New → Background Worker
- [ ] Connect same Git repository
- [ ] Build Command: `pip install -r requirements.txt`
- [ ] Start Command: `celery -A app.tasks.celery_app.celery_app worker --loglevel=info --concurrency=4`
- [ ] Add **same environment variables** as web service

### 5. Verify
- [ ] Check web service URL works
- [ ] Visit `/api/health` endpoint
- [ ] Check worker logs for errors
- [ ] Test CSV upload functionality

## Environment Variables Template

```bash
DATABASE_URL=postgresql://user:pass@host:5432/dbname
REDIS_URL=redis://red-xxxxx:6379
CELERY_BROKER_URL=redis://red-xxxxx:6379
CELERY_RESULT_BACKEND=redis://red-xxxxx:6379
SECRET_KEY=<generate-random-key>
DEBUG=false
ENVIRONMENT=production
```

## Important Notes

- Use **Internal URLs** (not external) for database and Redis
- All services must be in the **same region**
- Free tier services spin down after inactivity
- Database initialization runs automatically on web service start

