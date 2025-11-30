# Docker Setup Guide

## Prerequisites
- Docker Desktop installed and running
- Docker Compose v2 (included with Docker Desktop)

## Quick Start

1. **Start all services:**
   ```bash
   docker-compose up -d
   ```

2. **Check service status:**
   ```bash
   docker-compose ps
   ```

3. **View logs:**
   ```bash
   # All services
   docker-compose logs -f
   
   # Specific service
   docker-compose logs -f web
   docker-compose logs -f celery
   docker-compose logs -f db
   docker-compose logs -f redis
   ```

4. **Access the application:**
   - Web UI: http://localhost:8000
   - API Health: http://localhost:8000/api/health
   - Database: localhost:5432
   - Redis: localhost:6379

## Services

- **web**: FastAPI application (port 8000)
- **celery**: Celery worker for async tasks
- **db**: PostgreSQL database (port 5432)
- **redis**: Redis for Celery broker and caching (port 6379)

## Troubleshooting

### If containers fail to start:

1. **Check Docker Desktop is running:**
   ```bash
   docker ps
   ```

2. **Restart Docker Desktop** if you see I/O errors

3. **Clean up and restart:**
   ```bash
   docker-compose down
   docker-compose up -d --build
   ```

4. **Check logs for errors:**
   ```bash
   docker-compose logs
   ```

### Database initialization:
The database tables are automatically created when the web service starts.

### Manual database initialization:
```bash
docker-compose exec web python init_db.py
```

## Stop Services

```bash
docker-compose down
```

## Stop and Remove Volumes (Clean Slate)

```bash
docker-compose down -v
```

## Environment Variables

All configuration is set in `docker-compose.yml`. To customize, edit the environment section of each service.

