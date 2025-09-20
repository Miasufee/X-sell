from datetime import datetime
from typing import Optional
from pydantic import EmailStr, field_validator
from .schema_base import BaseSchema, IDSchema, TimestampSchema
from ..models.merchant import MerchantApplicationStatus


class MerchantApplicationBase(BaseSchema):
    business_name: str
    business_description: str
    business_address: str
    business_phone: str
    business_email: EmailStr
    tax_id: Optional[str] = None
    website_url: Optional[str] = None

    @field_validator('website_url')
    def validate_website_url(cls, v):
        if v and not v.startswith(('http://', 'https://')):
            raise ValueError('Website URL must start with http:// or https://')
        return v


class MerchantApplicationCreate(MerchantApplicationBase):
    pass


class MerchantApplicationUpdate(BaseSchema):
    business_name: Optional[str] = None
    business_description: Optional[str] = None
    business_address: Optional[str] = None
    business_phone: Optional[str] = None
    business_email: Optional[EmailStr] = None
    tax_id: Optional[str] = None
    website_url: Optional[str] = None


class MerchantApplicationResponse(MerchantApplicationBase, IDSchema, TimestampSchema):
    status: MerchantApplicationStatus
    rejection_reason: Optional[str] = None
    admin_notes: Optional[str] = None
    approved_at: Optional[datetime] = None
    user_id: int
    approved_by: Optional[int] = None


class MerchantApplicationStatusUpdate(BaseSchema):
    status: MerchantApplicationStatus
    reason: Optional[str] = None
    notes: Optional[str] = None


class MerchantApplicationStats(BaseSchema):
    pending_count: int
    approved_count: int
    rejected_count: int
    suspended_count: int
    total_count: int
    recent_count: int


class MerchantApplicationSearch(BaseSchema):
    search_term: Optional[str] = None
    status: Optional[MerchantApplicationStatus] = None
    min_date: Optional[datetime] = None
    max_date: Optional[datetime] = None
    page: int = 1
    per_page: int = 20