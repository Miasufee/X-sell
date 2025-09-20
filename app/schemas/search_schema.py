from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from app.schemas.product_schema import ProductResponse
from app.schemas.shop_schema import ShopResponse


class SearchQuery(BaseModel):
    q: str = Field(..., min_length=1, max_length=200, description="Search query")
    category_id: Optional[int] = None
    min_price: Optional[float] = Field(None, ge=0)
    max_price: Optional[float] = Field(None, ge=0)
    in_stock: Optional[bool] = None
    merchant_id: Optional[int] = None
    shop_id: Optional[int] = None
    location_lat: Optional[float] = Field(None, ge=-90, le=90)
    location_lng: Optional[float] = Field(None, ge=-180, le=180)
    radius_km: Optional[int] = Field(None, ge=1, le=50)
    sort_by: str = Field(
        "relevance",
        pattern="^(relevance|price|distance|popularity|newest)$",
        description="Sorting method"
    )
    sort_order: str = Field(
        "desc",
        pattern="^(asc|desc)$",
        description="Sort order"
    )


class SearchResult(BaseModel):
    product: ProductResponse
    relevance_score: float
    distance_km: Optional[float] = None
    shop: Optional[ShopResponse] = None


class SearchResponse(BaseModel):
    results: List[SearchResult]
    total: int
    query: str
    filters_applied: Dict[str, Any]
    search_time_ms: int
    suggestions: List[str] = []


class RecommendationRequest(BaseModel):
    user_id: Optional[int] = None
    product_id: Optional[int] = None
    category_id: Optional[int] = None
    limit: int = Field(10, ge=1, le=50)


class RecommendationResponse(BaseModel):
    products: List[ProductResponse]
    recommendation_type: str
    based_on: Dict[str, Any]
    total: int


class TrendingProductsResponse(BaseModel):
    products: List[ProductResponse]
    period: str
    total: int

