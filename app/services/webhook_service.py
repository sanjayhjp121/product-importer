"""Webhook service for triggering webhooks."""
import httpx
import asyncio
from typing import List, Dict, Optional
from app.models import Webhook, WebhookEventType
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)


async def trigger_webhook(webhook: Webhook, payload: Dict, timeout: int = 10) -> Dict:
    """
    Trigger a webhook asynchronously.
    
    Args:
        webhook: Webhook configuration
        payload: Data to send
        timeout: Request timeout in seconds
        
    Returns:
        Dictionary with response details
    """
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            start_time = asyncio.get_event_loop().time()
            response = await client.post(
                webhook.url,
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            end_time = asyncio.get_event_loop().time()
            response_time_ms = (end_time - start_time) * 1000
            
            return {
                "success": 200 <= response.status_code < 300,
                "status_code": response.status_code,
                "response_time_ms": response_time_ms,
                "response_body": response.text[:500],  # Limit response body length
                "error": None
            }
    except httpx.TimeoutException:
        return {
            "success": False,
            "status_code": None,
            "response_time_ms": None,
            "response_body": None,
            "error": "Request timeout"
        }
    except Exception as e:
        logger.error(f"Webhook error for {webhook.url}: {str(e)}")
        return {
            "success": False,
            "status_code": None,
            "response_time_ms": None,
            "response_body": None,
            "error": str(e)
        }


async def trigger_webhooks_for_event(
    db: Session,
    event_type: WebhookEventType,
    payload: Dict
) -> List[Dict]:
    """
    Trigger all enabled webhooks for a specific event type.
    
    Args:
        db: Database session
        event_type: Type of event
        payload: Data to send
        
    Returns:
        List of webhook results
    """
    webhooks = db.query(Webhook).filter(
        Webhook.event_type == event_type,
        Webhook.enabled == True
    ).all()
    
    if not webhooks:
        return []
    
    # Trigger all webhooks concurrently
    tasks = [trigger_webhook(webhook, payload) for webhook in webhooks]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Convert exceptions to error dicts
    processed_results = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            processed_results.append({
                "success": False,
                "status_code": None,
                "response_time_ms": None,
                "response_body": None,
                "error": str(result)
            })
        else:
            processed_results.append(result)
    
    return processed_results


def trigger_webhooks_sync(
    db: Session,
    event_type: WebhookEventType,
    payload: Dict
) -> List[Dict]:
    """
    Synchronous wrapper for triggering webhooks.
    Use this in Celery tasks or other sync contexts.
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(trigger_webhooks_for_event(db, event_type, payload))
    finally:
        loop.close()

