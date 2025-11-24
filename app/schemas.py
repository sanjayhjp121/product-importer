"""Pydantic schemas for request/response validation."""
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from app.models import WebhookEventType


class ProductBase(BaseModel):
    """Base product schema."""
    sku: str = Field(..., min_length=1, max_length=255)
    name: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None
    active: bool = True
    
    @validator('sku')
    def sku_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('SKU cannot be empty')
        return v.strip()


class ProductCreate(ProductBase):
    """Schema for creating a product."""
    pass


class ProductUpdate(BaseModel):
    """Schema for updating a product."""
    name: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = None
    active: Optional[bool] = None


class ProductResponse(ProductBase):
    """Schema for product response."""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ProductListResponse(BaseModel):
    """Schema for paginated product list response."""
    items: List[ProductResponse]
    total: int
    page: int
    per_page: int
    pages: int


class WebhookBase(BaseModel):
    """Base webhook schema."""
    url: str = Field(..., min_length=1, max_length=1000)
    event_type: WebhookEventType
    enabled: bool = True
    
    @validator('url')
    def url_must_be_valid(cls, v):
        if not v.startswith(('http://', 'https://')):
            raise ValueError('URL must start with http:// or https://')
        return v


class WebhookCreate(WebhookBase):
    """Schema for creating a webhook."""
    pass


class WebhookUpdate(BaseModel):
    """Schema for updating a webhook."""
    url: Optional[str] = Field(None, min_length=1, max_length=1000)
    event_type: Optional[WebhookEventType] = None
    enabled: Optional[bool] = None


class WebhookResponse(WebhookBase):
    """Schema for webhook response."""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class WebhookTestResponse(BaseModel):
    """Schema for webhook test response."""
    success: bool
    status_code: Optional[int] = None
    response_time_ms: Optional[float] = None
    response_body: Optional[str] = None
    error: Optional[str] = None


class UploadResponse(BaseModel):
    """Schema for upload response."""
    task_id: str
    message: str


class ProgressResponse(BaseModel):
    """Schema for progress response."""
    task_id: str
    status: str
    progress: int
    total: int
    percentage: float
    message: Optional[str] = None
    errors: List[str] = []

