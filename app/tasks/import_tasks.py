"""Celery tasks for CSV import."""
import os
import json
import redis
from typing import List
from app.tasks.celery_app import celery_app
from app.database import SessionLocal
from app.services.csv_processor import parse_csv_file, validate_csv_row, row_to_product_dict
from app.services.product_service import bulk_upsert_products
from app.services.webhook_service import trigger_webhooks_sync
from app.models import WebhookEventType
from app.config import settings
import logging

logger = logging.getLogger(__name__)

# Redis connection for progress tracking
redis_client = redis.from_url(settings.REDIS_URL)


def update_progress(task_id: str, status: str, progress: int, total: int, message: str = None, errors: List[str] = None):
    """Update progress in Redis."""
    progress_data = {
        "status": status,
        "progress": progress,
        "total": total,
        "percentage": (progress / total * 100) if total > 0 else 0,
        "message": message or "",
        "errors": errors or []
    }
    redis_client.setex(f"import_progress:{task_id}", 3600, json.dumps(progress_data))  # 1 hour TTL


@celery_app.task(bind=True, name="import_products")
def import_products_task(self, task_id: str, file_path: str):
    """
    Celery task to import products from CSV file.
    
    Args:
        task_id: Unique task identifier
        file_path: Path to uploaded CSV file
    """
    db = SessionLocal()
    errors = []
    processed = 0
    created = 0
    updated = 0
    
    try:
        # Read file
        update_progress(task_id, "reading", 0, 0, "Reading CSV file...")
        
        with open(file_path, 'rb') as f:
            file_content = f.read()
        
        # Parse CSV
        update_progress(task_id, "parsing", 0, 0, "Parsing CSV file...")
        rows = list(parse_csv_file(file_content))
        total_rows = len(rows)
        
        if total_rows == 0:
            update_progress(task_id, "error", 0, 0, "CSV file is empty", [])
            return
        
        update_progress(task_id, "validating", 0, total_rows, f"Validating {total_rows} rows...")
        
        # Validate and prepare products
        products_to_import = []
        for idx, row in enumerate(rows, start=1):
            is_valid, error_msg = validate_csv_row(row, idx)
            if not is_valid:
                errors.append(error_msg)
                continue
            
            try:
                product_dict = row_to_product_dict(row)
                products_to_import.append(product_dict)
            except Exception as e:
                errors.append(f"Row {idx}: {str(e)}")
                continue
        
        # Process in chunks
        update_progress(task_id, "importing", 0, len(products_to_import), "Importing products...")
        
        chunk_size = 1000
        for i in range(0, len(products_to_import), chunk_size):
            chunk = products_to_import[i:i + chunk_size]
            chunk_created, chunk_updated = bulk_upsert_products(db, chunk)
            created += chunk_created
            updated += chunk_updated
            processed += len(chunk)
            
            # Update progress
            progress_msg = f"Imported {processed}/{len(products_to_import)} products..."
            update_progress(task_id, "importing", processed, len(products_to_import), progress_msg, errors)
        
        # Trigger webhook for import completion
        try:
            trigger_webhooks_sync(
                db,
                WebhookEventType.IMPORT_COMPLETED,
                {
                    "task_id": task_id,
                    "total_rows": total_rows,
                    "processed": processed,
                    "created": created,
                    "updated": updated,
                    "errors": len(errors)
                }
            )
        except Exception as e:
            logger.error(f"Error triggering webhook: {str(e)}")
        
        # Final status
        final_message = f"Import complete! Created: {created}, Updated: {updated}, Errors: {len(errors)}"
        update_progress(task_id, "completed", processed, len(products_to_import), final_message, errors)
        
    except Exception as e:
        logger.error(f"Import task error: {str(e)}", exc_info=True)
        update_progress(task_id, "error", processed, 0, f"Import failed: {str(e)}", errors + [str(e)])
    finally:
        db.close()
        # Clean up file
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            logger.error(f"Error cleaning up file: {str(e)}")

