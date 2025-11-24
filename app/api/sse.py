"""Server-Sent Events endpoint for progress streaming."""
import json
import asyncio
import redis
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.config import settings

router = APIRouter(prefix="/api", tags=["progress"])

# Redis connection for progress tracking
redis_client = redis.from_url(settings.REDIS_URL)


@router.get("/stream/{task_id}")
async def stream_progress(task_id: str):
    """
    SSE endpoint for real-time progress updates.
    """
    async def event_generator():
        last_progress = -1
        error_count = 0
        max_errors = 10
        
        while True:
            # Get progress from Redis
            progress_key = f"import_progress:{task_id}"
            progress_data = redis_client.get(progress_key)
            
            if progress_data:
                try:
                    # Parse progress data (stored as JSON)
                    progress_dict = json.loads(progress_data.decode('utf-8'))
                    
                    current_progress = progress_dict.get('progress', 0)
                    status = progress_dict.get('status', 'unknown')
                    
                    # Send update if progress changed
                    if current_progress != last_progress or status in ['completed', 'error']:
                        yield f"data: {json.dumps(progress_dict)}\n\n"
                        last_progress = current_progress
                        
                        # Stop if completed or error
                        if status in ['completed', 'error']:
                            break
                    
                    error_count = 0  # Reset error count on successful read
                except Exception as e:
                    error_count += 1
                    if error_count >= max_errors:
                        yield f"data: {json.dumps({'status': 'error', 'message': 'Failed to parse progress data'})}\n\n"
                        break
            else:
                # No progress data yet, wait a bit
                error_count += 1
                if error_count >= max_errors:
                    yield f"data: {json.dumps({'status': 'error', 'message': 'Task not found or expired'})}\n\n"
                    break
            
            # Wait before next check
            await asyncio.sleep(1)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.get("/progress/{task_id}")
async def get_progress(task_id: str):
    """
    Get current progress for a task (polling fallback).
    """
    progress_key = f"import_progress:{task_id}"
    progress_data = redis_client.get(progress_key)
    
    if not progress_data:
        raise HTTPException(status_code=404, detail="Task not found or expired")
    
    try:
        progress_dict = json.loads(progress_data.decode('utf-8'))
        return progress_dict
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error parsing progress data: {str(e)}")

