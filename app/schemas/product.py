from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from app.models.product import ProductStatus


class ProductImageBase(BaseModel):
    url: str
    alt_text: Optional[str] = None
    is_primary: bool = False
    sort_order: int = 0


class ProductImageCreate(ProductImageBase):
    pass


class ProductImageResponse(ProductImageBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class ProductBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1)
    price: float = Field(..., gt=0)
    stock_quantity: int = Field(..., ge=0)
    sku: Optional[str] = Field(None, max_length=100)
    tags: Optional[List[str]] = []
    weight: Optional[float] = Field(None, gt=0)
    is_featured: bool = False
    category_id: int
    shop_id: int


class ProductCreate(ProductBase):
    status: ProductStatus = ProductStatus.DRAFT


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    price: Optional[float] = Field(None, gt=0)
    stock_quantity: Optional[int] = Field(None, ge=0)
    sku: Optional[str] = Field(None, max_length=100)
    tags: Optional[List[str]] = None
    weight: Optional[float] = Field(None, gt=0)
    is_featured: Optional[bool] = None
    status: Optional[ProductStatus] = None
    category_id: Optional[int] = None
    shop_id: Optional[int] = None


class ProductResponse(ProductBase):
    id: int
    status: ProductStatus
    view_count: int
    merchant_id: int
    created_at: datetime
    updated_at: datetime
    images: List[ProductImageResponse] = []

    class Config:
        from_attributes = True


class ProductListResponse(BaseModel):
    id: int
    name: str
    price: float
    stock_quantity: int
    status: ProductStatus
    is_featured: bool
    view_count: int
    primary_image: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ProductFilter(BaseModel):
    category_id: Optional[int] = None
    shop_id: Optional[int] = None
    merchant_id: Optional[int] = None
    status: Optional[ProductStatus] = None
    is_featured: Optional[bool] = None
    min_price: Optional[float] = Field(None, ge=0)
    max_price: Optional[float] = Field(None, ge=0)
    in_stock: Optional[bool] = None
    search: Optional[str] = None

    @validator('max_price')
    def validate_price_range(cls, v, values):
        if v is not None and 'min_price' in values and values['min_price'] is not None:
            if v < values['min_price']:
                raise ValueError('max_price must be greater than or equal to min_price')
        return v
