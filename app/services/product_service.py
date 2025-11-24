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
    Bulk upsert products using PostgreSQL INSERT ... ON CONFLICT.
    Uses the case-insensitive unique index on lower(sku).
    
    Returns:
        Tuple of (created_count, updated_count)
    """
    if not products:
        return 0, 0
    
    # Check existing SKUs (case-insensitive) before bulk operation
    skus_lower = {p['sku'].lower() for p in products}
    existing_products = db.query(Product).filter(
        func.lower(Product.sku).in_(skus_lower)
    ).all()
    existing_skus_lower = {p.sku.lower() for p in existing_products}
    
    # Separate into inserts and updates
    to_insert = []
    to_update_map = {}
    
    for p in products:
        sku_lower = p['sku'].lower()
        if sku_lower in existing_skus_lower:
            # Find the existing product (case-insensitive match)
            existing = next(ep for ep in existing_products if ep.sku.lower() == sku_lower)
            to_update_map[existing.id] = p
        else:
            to_insert.append(p)
    
    # Bulk insert new products
    if to_insert:
        db.bulk_insert_mappings(Product, to_insert)
    
    # Bulk update existing products
    if to_update_map:
        update_mappings = []
        for product_id, product_data in to_update_map.items():
            update_data = {k: v for k, v in product_data.items() if k != 'sku'}
            update_data['id'] = product_id
            update_mappings.append(update_data)
        db.bulk_update_mappings(Product, update_mappings)
    
    # Single commit for all operations
    db.commit()
    
    return len(to_insert), len(to_update_map)


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

