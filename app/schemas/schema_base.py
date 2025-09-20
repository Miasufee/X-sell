from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Generic, TypeVar, List

T = TypeVar('T')

class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

class IDSchema(BaseSchema):
    id: int

class TimestampSchema(BaseSchema):
    created_at: datetime
    updated_at: datetime

class PaginatedResponse(BaseSchema, Generic[T]):
    items: List[T]
    total: int
    page: int
    per_page: int
    total_pages: int
    has_next: bool
    has_prev: bool