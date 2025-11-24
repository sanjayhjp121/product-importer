"""Product CRUD endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.models import Product
from app.schemas import (
    ProductCreate, ProductUpdate, ProductResponse, ProductListResponse
)
from app.services.product_service import (
    get_product_by_sku, create_product, update_product,
    get_products, delete_all_products
)
from app.services.webhook_service import trigger_webhooks_sync
from app.models import WebhookEventType
import math

router = APIRouter(prefix="/api/products", tags=["products"])


@router.get("", response_model=ProductListResponse)
def list_products(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    sku: Optional[str] = None,
    name: Optional[str] = None,
    description: Optional[str] = None,
    active: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """List products with pagination and filtering."""
    products, total = get_products(
        db=db,
        page=page,
        per_page=per_page,
        sku_filter=sku,
        name_filter=name,
        description_filter=description,
        active_filter=active
    )
    
    pages = math.ceil(total / per_page) if total > 0 else 0
    
    return ProductListResponse(
        items=[ProductResponse.model_validate(p) for p in products],
        total=total,
        page=page,
        per_page=per_page,
        pages=pages
    )


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db)):
    """Get a single product by ID."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return ProductResponse.model_validate(product)


@router.post("", response_model=ProductResponse, status_code=201)
def create_product_endpoint(product: ProductCreate, db: Session = Depends(get_db)):
    """Create a new product."""
    # Check if SKU already exists (case-insensitive)
    existing = get_product_by_sku(db, product.sku)
    if existing:
        raise HTTPException(status_code=400, detail="Product with this SKU already exists")
    
    product_data = product.model_dump()
    new_product = create_product(db, product_data)
    
    # Trigger webhook
    try:
        trigger_webhooks_sync(
            db,
            WebhookEventType.PRODUCT_CREATED,
            ProductResponse.model_validate(new_product).model_dump()
        )
    except Exception:
        pass  # Don't fail if webhook fails
    
    return ProductResponse.model_validate(new_product)


@router.put("/{product_id}", response_model=ProductResponse)
def update_product_endpoint(
    product_id: int,
    product_update: ProductUpdate,
    db: Session = Depends(get_db)
):
    """Update an existing product."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    update_data = product_update.model_dump(exclude_unset=True)
    updated_product = update_product(db, product, update_data)
    
    # Trigger webhook
    try:
        trigger_webhooks_sync(
            db,
            WebhookEventType.PRODUCT_UPDATED,
            ProductResponse.model_validate(updated_product).model_dump()
        )
    except Exception:
        pass  # Don't fail if webhook fails
    
    return ProductResponse.model_validate(updated_product)


@router.delete("/{product_id}", status_code=204)
def delete_product(product_id: int, db: Session = Depends(get_db)):
    """Delete a product."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    product_data = ProductResponse.model_validate(product).model_dump()
    db.delete(product)
    db.commit()
    
    # Trigger webhook
    try:
        trigger_webhooks_sync(
            db,
            WebhookEventType.PRODUCT_DELETED,
            product_data
        )
    except Exception:
        pass  # Don't fail if webhook fails
    
    return None


@router.delete("/bulk/all", status_code=200)
def bulk_delete_products(db: Session = Depends(get_db)):
    """Delete all products."""
    count = delete_all_products(db)
    return {"message": f"Deleted {count} products", "count": count}

