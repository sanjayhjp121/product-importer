# Render Deployment Guide

This guide will walk you through deploying the Product Importer application on Render.com.

## Prerequisites

1. A Render.com account (sign up at https://render.com)
2. Your code pushed to a Git repository (GitHub, GitLab, or Bitbucket)

## Deployment Steps

### Step 1: Create PostgreSQL Database

1. Log in to your Render dashboard
2. Click **"New +"** → **"PostgreSQL"**
3. Configure the database:
   - **Name**: `product-importer-db` (or any name you prefer)
   - **Database**: `product_importer`
   - **User**: `product_user` (or any username)
   - **Region**: Choose closest to your users
   - **Plan**: Start with **Starter** (free tier available, but limited)
4. Click **"Create Database"**
5. **Important**: Copy the **Internal Database URL** - you'll need this later

### Step 2: Create Redis Instance

1. In Render dashboard, click **"New +"** → **"Redis"**
2. Configure Redis:
   - **Name**: `product-importer-redis` (or any name you prefer)
   - **Region**: Same region as your database
   - **Plan**: Start with **Starter** (free tier available)
3. Click **"Create Redis"**
4. **Important**: Copy the **Internal Redis URL** - you'll need this later

### Step 3: Deploy Web Service

1. In Render dashboard, click **"New +"** → **"Web Service"**
2. Connect your Git repository
3. Configure the service:
   - **Name**: `product-importer-web`
   - **Environment**: `Python 3`
   - **Region**: Same as database
   - **Branch**: `main` (or your default branch)
   - **Root Directory**: Leave empty (or `.` if needed)
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python init_db.py && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Click **"Advanced"** and add environment variables:
   - `DATABASE_URL`: Paste the Internal Database URL from Step 1
   - `REDIS_URL`: Paste the Internal Redis URL from Step 2
   - `CELERY_BROKER_URL`: Same as `REDIS_URL`
   - `CELERY_RESULT_BACKEND`: Same as `REDIS_URL`
   - `SECRET_KEY`: Generate a random secret key (you can use: `openssl rand -hex 32`)
   - `DEBUG`: `false`
   - `ENVIRONMENT`: `production`
   - `PORT`: `10000` (Render sets this automatically, but good to have as fallback)
5. Click **"Create Web Service"**

### Step 4: Deploy Celery Worker

1. In Render dashboard, click **"New +"** → **"Background Worker"**
2. Connect the same Git repository
3. Configure the worker:
   - **Name**: `product-importer-worker`
   - **Environment**: `Python 3`
   - **Region**: Same as other services
   - **Branch**: `main` (or your default branch)
   - **Root Directory**: Leave empty
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `celery -A app.tasks.celery_app.celery_app worker --loglevel=info --concurrency=4`
4. Click **"Advanced"** and add the **same environment variables** as the web service:
   - `DATABASE_URL`: Same as web service
   - `REDIS_URL`: Same as web service
   - `CELERY_BROKER_URL`: Same as web service
   - `CELERY_RESULT_BACKEND`: Same as web service
   - `SECRET_KEY`: Same as web service
   - `DEBUG`: `false`
   - `ENVIRONMENT`: `production`
5. Click **"Create Background Worker"**

### Step 5: Using render.yaml (Alternative Method)

If you prefer to use the `render.yaml` file for infrastructure as code:

1. Push your code with `render.yaml` to your repository
2. In Render dashboard, click **"New +"** → **"Blueprint"**
3. Connect your repository
4. Render will automatically detect `render.yaml` and create all services
5. **Important**: You'll still need to manually set the Redis URL environment variables since Redis isn't directly supported in render.yaml

### Step 6: Link Services (if using render.yaml)

After services are created via render.yaml:

1. Go to each service (web and worker)
2. In **Environment** section, update:
   - `REDIS_URL`: Add the Internal Redis URL from your Redis instance
   - `CELERY_BROKER_URL`: Same as `REDIS_URL`
   - `CELERY_RESULT_BACKEND`: Same as `REDIS_URL`
3. The `DATABASE_URL` should be automatically linked if configured correctly in render.yaml

## Environment Variables Summary

All services (web and worker) need these environment variables:

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@host:5432/dbname` |
| `REDIS_URL` | Redis connection string | `redis://red-xxxxx:6379` |
| `CELERY_BROKER_URL` | Same as REDIS_URL | `redis://red-xxxxx:6379` |
| `CELERY_RESULT_BACKEND` | Same as REDIS_URL | `redis://red-xxxxx:6379` |
| `SECRET_KEY` | Random secret for app security | Generated string |
| `DEBUG` | Debug mode (false in production) | `false` |
| `ENVIRONMENT` | Environment name | `production` |

## Database Initialization

The database tables are automatically created when the web service starts (via `init_db.py` in the start command). If you need to manually initialize:

1. Connect to your database via Render's database dashboard
2. Or use Render's shell: `render shell` → `python init_db.py`

## Verifying Deployment

1. **Check Web Service**: Visit your web service URL (provided by Render)
2. **Health Check**: Visit `https://your-app.onrender.com/api/health` - should return `{"status": "healthy"}`
3. **Check Worker Logs**: In Render dashboard, check the worker service logs for any errors
4. **Test Upload**: Try uploading a CSV file through the web interface

## Troubleshooting

### Database Connection Issues
- Verify `DATABASE_URL` uses the **Internal Database URL** (not external)
- Check that database is in the same region as services
- Ensure database is not paused (free tier databases pause after inactivity)

### Redis Connection Issues
- Verify `REDIS_URL` uses the **Internal Redis URL**
- Check that Redis is in the same region
- Ensure Redis is not paused

### Worker Not Processing Tasks
- Verify worker service is running (check logs)
- Ensure `CELERY_BROKER_URL` and `CELERY_RESULT_BACKEND` are set correctly
- Check that Redis is accessible from worker service

### Build Failures
- Check `requirements.txt` is correct
- Verify Python version in `runtime.txt` matches Render's supported versions
- Check build logs for specific error messages

## Cost Considerations

- **Free Tier**: Limited hours per month, services spin down after inactivity
- **Starter Plan**: $7/month per service (web, worker, database, redis = ~$28/month)
- **Production**: Consider higher plans for better performance and uptime

## Security Notes

1. **SECRET_KEY**: Always use a strong, randomly generated secret key in production
2. **CORS**: Update CORS settings in `app/main.py` to restrict origins in production
3. **Database**: Use Internal Database URLs (not external) for better security
4. **Environment Variables**: Never commit secrets to Git

## Next Steps

After deployment:
1. Set up custom domain (optional)
2. Configure webhooks for production URLs
3. Set up monitoring and alerts
4. Configure backups for database
5. Review and optimize for production workloads

