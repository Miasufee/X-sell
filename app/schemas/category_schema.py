from typing import Optional, List
from pydantic import field_validator
from .schema_base import BaseSchema, IDSchema, TimestampSchema


class CategoryBase(BaseSchema):
    name: str
    slug: str
    description: Optional[str] = None
    is_active: bool = True

    @field_validator('slug')
    def validate_slug(cls, v):
        if not v.replace('-', '').replace('_', '').isalnum():
            raise ValueError('Slug can only contain alphanumeric characters, hyphens, and underscores')
        return v.lower()


class CategoryCreate(CategoryBase):
    parent_id: Optional[int] = None


class CategoryUpdate(BaseSchema):
    name: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    parent_id: Optional[int] = None


class CategoryResponse(CategoryBase, IDSchema, TimestampSchema):
    parent_id: Optional[int] = None
    product_count: Optional[int] = None


class CategoryWithChildrenResponse(CategoryResponse):
    children: List['CategoryResponse'] = []
    subcategories: List['SubCategoryResponse'] = []


class SubCategoryBase(BaseSchema):
    name: str
    slug: str
    description: Optional[str] = None
    is_active: bool = True


class SubCategoryCreate(SubCategoryBase):
    category_id: int


class SubCategoryUpdate(BaseSchema):
    name: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class SubCategoryResponse(SubCategoryBase, IDSchema, TimestampSchema):
    category_id: int
    product_count: Optional[int] = None


class SubCategoryWithCategoryResponse(SubCategoryResponse):
    category: Optional[CategoryResponse] = None


class CategoryTreeResponse(BaseSchema):
    categories: List[CategoryWithChildrenResponse]


class CategorySearch(BaseSchema):
    search_term: Optional[str] = None
    active_only: bool = True
    page: int = 1
    per_page: int = 20


class SubCategorySearch(BaseSchema):
    search_term: Optional[str] = None
    category_id: Optional[int] = None
    active_only: bool = True
    page: int = 1
    per_page: int = 20


class CategoryStats(BaseSchema):
    total_categories: int
    active_categories: int
    top_level_categories: int


class SubCategoryStats(BaseSchema):
    total_subcategories: int
    active_subcategories: int


# Update forward references
CategoryWithChildrenResponse.model_rebuild()