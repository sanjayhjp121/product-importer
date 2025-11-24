"""Product service for business logic."""
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from typing import Optional, List, Dict
from app.models import Product


def get_product_by_sku(db: Session, sku: str) -> Optional[Product]:
    """Get product by SKU (case-insensitive)."""
    return db.query(Product).filter(func.lower(Product.sku) == func.lower(sku)).first()


def create_product(db: Session, product_data: Dict) -> Product:
    """Create a new product."""
    product = Product(**product_data)
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def update_product(db: Session, product: Product, product_data: Dict) -> Product:
    """Update an existing product."""
    for key, value in product_data.items():
        setattr(product, key, value)
    db.commit()
    db.refresh(product)
    return product


def upsert_product(db: Session, product_data: Dict) -> Product:
    """
    Upsert a product (insert or update based on SKU).
    Uses case-insensitive SKU matching.
    """
    sku = product_data['sku']
    existing = get_product_by_sku(db, sku)
    
    if existing:
        # Update existing product
        for key, value in product_data.items():
            if key != 'sku':  # Don't update SKU
                setattr(existing, key, value)
        db.commit()
        db.refresh(existing)
        return existing
    else:
        # Create new product
        return create_product(db, product_data)


def bulk_upsert_products(db: Session, products: List[Dict]) -> tuple[int, int]:
    """
    Bulk upsert products using PostgreSQL ON CONFLICT.
    
    Returns:
        Tuple of (created_count, updated_count)
    """
    if not products:
        return 0, 0
    
    created = 0
    updated = 0
    
    # Process in chunks to avoid memory issues
    chunk_size = 1000
    for i in range(0, len(products), chunk_size):
        chunk = products[i:i + chunk_size]
        
        # Use individual upserts for case-insensitive matching
        for product_data in chunk:
            existing = get_product_by_sku(db, product_data['sku'])
            if existing:
                update_product(db, existing, {k: v for k, v in product_data.items() if k != 'sku'})
                updated += 1
            else:
                create_product(db, product_data)
                created += 1
    
    return created, updated


def get_products(
    db: Session,
    page: int = 1,
    per_page: int = 50,
    sku_filter: Optional[str] = None,
    name_filter: Optional[str] = None,
    description_filter: Optional[str] = None,
    active_filter: Optional[bool] = None
) -> tuple[List[Product], int]:
    """
    Get paginated products with optional filters.
    
    Returns:
        Tuple of (products_list, total_count)
    """
    query = db.query(Product)
    
    # Apply filters
    if sku_filter:
        query = query.filter(Product.sku.ilike(f"%{sku_filter}%"))
    
    if name_filter:
        query = query.filter(Product.name.ilike(f"%{name_filter}%"))
    
    if description_filter:
        query = query.filter(Product.description.ilike(f"%{description_filter}%"))
    
    if active_filter is not None:
        query = query.filter(Product.active == active_filter)
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    offset = (page - 1) * per_page
    products = query.order_by(Product.id.desc()).offset(offset).limit(per_page).all()
    
    return products, total


def delete_all_products(db: Session) -> int:
    """Delete all products and return count."""
    count = db.query(Product).delete()
    db.commit()
    return count

