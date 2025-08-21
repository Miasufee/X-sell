from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from app.models.order import OrderStatus
from app.schemas.product import ProductListResponse


class OrderItemResponse(BaseModel):
    id: int
    product_id: int
    product_name: str
    product_sku: Optional[str]
    quantity: int
    unit_price: float
    total_price: float
    product: Optional[ProductListResponse] = None

    class Config:
        from_attributes = True


class OrderResponse(BaseModel):
    id: int
    order_number: str
    status: OrderStatus
    subtotal: float
    tax_amount: float
    delivery_fee: float
    total_amount: float
    delivery_address: str
    notes: Optional[str]
    items: List[OrderItemResponse]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class OrderListResponse(BaseModel):
    id: int
    order_number: str
    status: OrderStatus
    total_amount: float
    items_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class CheckoutRequest(BaseModel):
    delivery_address: str = Field(..., min_length=10)
    notes: Optional[str] = None
    delivery_lat: Optional[float] = Field(None, ge=-90, le=90)
    delivery_lng: Optional[float] = Field(None, ge=-180, le=180)


class OrderStatusUpdate(BaseModel):
    status: OrderStatus
    notes: Optional[str] = None
