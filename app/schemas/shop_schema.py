# app/schemas/shop_crud.py
from typing import Optional
from pydantic import EmailStr, field_validator
from .schema_base import BaseSchema, IDSchema, TimestampSchema


class ShopBase(BaseSchema):
    name: str
    description: Optional[str] = None
    address: str
    latitude: float
    longitude: float
    phone: Optional[str] = None
    email: Optional[EmailStr] = None

    @field_validator('latitude')
    def validate_latitude(cls, v):
        if not -90 <= v <= 90:
            raise ValueError('Latitude must be between -90 and 90')
        return v

    @field_validator('longitude')
    def validate_longitude(cls, v):
        if not -180 <= v <= 180:
            raise ValueError('Longitude must be between -180 and 180')
        return v


class ShopCreate(ShopBase):
    pass


class ShopUpdate(BaseSchema):
    name: Optional[str] = None
    description: Optional[str] = None
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None


class ShopResponse(ShopBase, IDSchema, TimestampSchema):
    is_active: bool
    merchant_id: int


class ShopWithMerchantResponse(ShopResponse):
    merchant: Optional[dict] = None  # Basic merchant info


class ShopSearch(BaseSchema):
    search_term: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    radius_km: float = 10.0
    active_only: bool = True
    page: int = 1
    per_page: int = 20


class ShopStats(BaseSchema):
    total_shops: int
    active_shops: int