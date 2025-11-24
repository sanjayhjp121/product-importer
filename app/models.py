"""SQLAlchemy database models."""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy import Index
import enum
import uuid
from app.database import Base


class WebhookEventType(str, enum.Enum):
    """Webhook event types."""
    PRODUCT_CREATED = "product.created"
    PRODUCT_UPDATED = "product.updated"
    PRODUCT_DELETED = "product.deleted"
    IMPORT_COMPLETED = "import.completed"


class Product(Base):
    """Product model."""
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String(255), nullable=False, unique=True, index=True)
    name = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    active = Column(Boolean, default=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Case-insensitive unique index on SKU
    __table_args__ = (
        Index('ix_products_sku_lower', func.lower(sku), unique=True),
    )
    
    def __repr__(self):
        return f"<Product(id={self.id}, sku='{self.sku}', name='{self.name}')>"


class Webhook(Base):
    """Webhook configuration model."""
    __tablename__ = "webhooks"
    
    id = Column(Integer, primary_key=True, index=True)
    url = Column(String(1000), nullable=False)
    event_type = Column(SQLEnum(WebhookEventType), nullable=False, index=True)
    enabled = Column(Boolean, default=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<Webhook(id={self.id}, url='{self.url}', event_type='{self.event_type}')>"

