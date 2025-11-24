"""Webhook management endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import Webhook, WebhookEventType
from app.schemas import (
    WebhookCreate, WebhookUpdate, WebhookResponse, WebhookTestResponse
)
from app.services.webhook_service import trigger_webhook
import asyncio

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])


@router.get("", response_model=List[WebhookResponse])
def list_webhooks(db: Session = Depends(get_db)):
    """List all webhooks."""
    webhooks = db.query(Webhook).order_by(Webhook.id.desc()).all()
    return [WebhookResponse.model_validate(w) for w in webhooks]


@router.get("/{webhook_id}", response_model=WebhookResponse)
def get_webhook(webhook_id: int, db: Session = Depends(get_db)):
    """Get a single webhook by ID."""
    webhook = db.query(Webhook).filter(Webhook.id == webhook_id).first()
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    return WebhookResponse.model_validate(webhook)


@router.post("", response_model=WebhookResponse, status_code=201)
def create_webhook(webhook: WebhookCreate, db: Session = Depends(get_db)):
    """Create a new webhook."""
    new_webhook = Webhook(**webhook.model_dump())
    db.add(new_webhook)
    db.commit()
    db.refresh(new_webhook)
    return WebhookResponse.model_validate(new_webhook)


@router.put("/{webhook_id}", response_model=WebhookResponse)
def update_webhook(
    webhook_id: int,
    webhook_update: WebhookUpdate,
    db: Session = Depends(get_db)
):
    """Update an existing webhook."""
    webhook = db.query(Webhook).filter(Webhook.id == webhook_id).first()
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    update_data = webhook_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(webhook, key, value)
    
    db.commit()
    db.refresh(webhook)
    return WebhookResponse.model_validate(webhook)


@router.delete("/{webhook_id}", status_code=204)
def delete_webhook(webhook_id: int, db: Session = Depends(get_db)):
    """Delete a webhook."""
    webhook = db.query(Webhook).filter(Webhook.id == webhook_id).first()
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    db.delete(webhook)
    db.commit()
    return None


@router.post("/{webhook_id}/test", response_model=WebhookTestResponse)
def test_webhook(webhook_id: int, db: Session = Depends(get_db)):
    """Test a webhook by sending a sample payload."""
    webhook = db.query(Webhook).filter(Webhook.id == webhook_id).first()
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    # Create sample payload based on event type
    sample_payloads = {
        WebhookEventType.PRODUCT_CREATED: {
            "event": "product.created",
            "data": {
                "id": 1,
                "sku": "TEST-SKU-001",
                "name": "Test Product",
                "description": "This is a test product",
                "active": True
            }
        },
        WebhookEventType.PRODUCT_UPDATED: {
            "event": "product.updated",
            "data": {
                "id": 1,
                "sku": "TEST-SKU-001",
                "name": "Updated Test Product",
                "description": "This is an updated test product",
                "active": True
            }
        },
        WebhookEventType.PRODUCT_DELETED: {
            "event": "product.deleted",
            "data": {
                "id": 1,
                "sku": "TEST-SKU-001",
                "name": "Deleted Test Product"
            }
        },
        WebhookEventType.IMPORT_COMPLETED: {
            "event": "import.completed",
            "data": {
                "task_id": "test-task-123",
                "total_rows": 100,
                "processed": 100,
                "created": 50,
                "updated": 50,
                "errors": 0
            }
        }
    }
    
    payload = sample_payloads.get(webhook.event_type, {"event": "test", "data": {}})
    
    # Trigger webhook
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(trigger_webhook(webhook, payload))
            return WebhookTestResponse(**result)
        finally:
            loop.close()
    except Exception as e:
        return WebhookTestResponse(
            success=False,
            error=str(e)
        )

