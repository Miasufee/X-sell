from datetime import datetime
from typing import Optional, List
from .schema_base import BaseSchema, IDSchema, TimestampSchema
from ..models import ProductStatus


class ProductBase(BaseSchema):
    name: str
    description: str
    tags: Optional[List[str]] = None
    is_featured: bool = False


class ProductCreate(ProductBase):
    category_id: int
    shop_id: int


class ProductUpdate(BaseSchema):
    name: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    status: Optional[ProductStatus] = None
    is_featured: Optional[bool] = None
    category_id: Optional[int] = None


class ProductResponse(ProductBase, IDSchema, TimestampSchema):
    status: ProductStatus
    view_count: int
    category_id: int
    shop_id: int
    merchant_id: int


class ProductImageBase(BaseSchema):
    url: str
    alt_text: Optional[str] = None
    is_primary: bool = False
    sort_order: int = 0


class ProductImageCreate(ProductImageBase):
    product_id: int


class ProductImageResponse(ProductImageBase, IDSchema, TimestampSchema):
    product_id: int


class ProductVariantBase(BaseSchema):
    sku: str
    price: float
    stock_quantity: int = 0
    weight: Optional[float] = None


class ProductVariantCreate(ProductVariantBase):
    product_id: int


class ProductVariantResponse(ProductVariantBase, IDSchema, TimestampSchema):
    product_id: int


class ProductAttributeBase(BaseSchema):
    name: str


class ProductAttributeValueBase(BaseSchema):
    value: str


class ProductSearch(BaseSchema):
    search_term: Optional[str] = None
    category_id: Optional[int] = None
    shop_id: Optional[int] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    status: Optional[ProductStatus] = None
    featured_only: bool = False
    page: int = 1
    per_page: int = 20


class ProductStats(BaseSchema):
    draft_count: int
    active_count: int
    inactive_count: int
    out_of_stock_count: int
    total_count: int
    featured_count: int

class ProductListResponse(BaseSchema):
    id: int
    name: str
    price: float
    stock_quantity: float
    status: str
    is_featured: bool
    view_count: int
    primary_image: str
    created_at: datetime