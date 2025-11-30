"""File upload endpoints."""
import os
import uuid
import json
import redis
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from app.config import settings
from app.schemas import UploadResponse
from app.tasks.import_tasks import import_products_task

router = APIRouter(prefix="/api/upload", tags=["upload"])


@router.post("", response_model=UploadResponse)
async def upload_csv(file: UploadFile = File(...)):
    """
    Upload CSV file for product import.
    
    Returns task_id immediately to avoid timeout.
    """
    # Validate file type
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV file")
    
    # Create upload directory if it doesn't exist
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    
    # Generate unique task ID and file path
    task_id = str(uuid.uuid4())
    file_path = os.path.join(settings.UPLOAD_DIR, f"{task_id}.csv")
    
    # Save file
    try:
        with open(file_path, "wb") as f:
            content = await file.read()
            
            # Check file size
            if len(content) > settings.MAX_UPLOAD_SIZE:
                raise HTTPException(
                    status_code=400,
                    detail=f"File size exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE / (1024*1024)}MB"
                )
            
            f.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving file: {str(e)}")
    
    # Initialize progress in Redis immediately
    redis_client = redis.from_url(settings.REDIS_URL)
    initial_progress = {
        "status": "queued",
        "progress": 0,
        "total": 0,
        "percentage": 0,
        "message": "Task queued, waiting to start...",
        "errors": []
    }
    redis_client.setex(f"import_progress:{task_id}", 3600, json.dumps(initial_progress))
    
    # Start Celery task
    try:
        import_products_task.delay(task_id, file_path)
    except Exception as e:
        # Clean up file and progress if task creation fails
        if os.path.exists(file_path):
            os.remove(file_path)
        redis_client.delete(f"import_progress:{task_id}")
        raise HTTPException(status_code=500, detail=f"Error starting import task: {str(e)}")
    
    return UploadResponse(
        task_id=task_id,
        message="File uploaded successfully. Import started."
    )

