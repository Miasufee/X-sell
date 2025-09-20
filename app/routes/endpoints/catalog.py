from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from app.core.database import get_db
from app.services.search import SearchService
from app.services.recommendation import RecommendationService
from app.schemas.search_schema import (
    SearchQuery, SearchResponse, SearchResult, 
    RecommendationRequest, RecommendationResponse, TrendingProductsResponse
)
from app.schemas.product_schema import ProductListResponse
from app.schemas.shop_schema import ShopResponse
from app.api.dependencies import get_current_user
from app.models.user import User

router = APIRouter()


@router.get("/search", response_model=SearchResponse)
async def search_catalog(
    q: str = Query(..., min_length=1, max_length=200, description="Search query"),
    category_id: Optional[int] = Query(None),
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    in_stock: Optional[bool] = Query(None),
    merchant_id: Optional[int] = Query(None),
    shop_id: Optional[int] = Query(None),
    location_lat: Optional[float] = Query(None, ge=-90, le=90),
    location_lng: Optional[float] = Query(None, ge=-180, le=180),
    radius_km: Optional[int] = Query(None, ge=1, le=50),
    sort_by: str = Query("relevance", regex="^(relevance|price|distance|popularity|newest)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """Advanced catalog search with filtering and ranking"""
    search_query = SearchQuery(
        q=q,
        category_id=category_id,
        min_price=min_price,
        max_price=max_price,
        in_stock=in_stock,
        merchant_id=merchant_id,
        shop_id=shop_id,
        location_lat=location_lat,
        location_lng=location_lng,
        radius_km=radius_km,
        sort_by=sort_by,
        sort_order=sort_order
    )
    
    service = SearchService(db)
    results, total, search_time_ms = await service.search_products(search_query, skip, limit)
    
    # Get search suggestions
    suggestions = await service.get_search_suggestions(q)
    
    # Convert results to response format
    search_results = []
    for item in results:
        product = item['product']
        shop = item['shop']
        
        # Get primary image
        primary_image = None
        if product.images:
            primary_img = next((img for img in product.images if img.is_primary), None)
            primary_image = primary_img.url if primary_img else product.images[0].url
        
        product_response = ProductListResponse(
            id=product.id,
            name=product.name,
            price=product.price,
            stock_quantity=product.stock_quantity,
            status=product.status,
            is_featured=product.is_featured,
            view_count=product.view_count,
            primary_image=primary_image,
            created_at=product.created_at
        )
        
        shop_response = ShopResponse(
            id=shop.id,
            name=shop.name,
            description=shop.description,
            address=shop.address,
            latitude=shop.latitude,
            longitude=shop.longitude,
            phone=shop.phone,
            email=shop.email,
            merchant_id=shop.merchant_id,
            is_active=shop.is_active,
            created_at=shop.created_at,
            updated_at=shop.updated_at
        )
        
        search_result = SearchResult(
            product=product_response,
            relevance_score=item['relevance_score'],
            distance_km=item['distance_km'],
            shop=shop_response
        )
        search_results.append(search_result)
    
    # Build filters applied
    filters_applied = {
        "query": q,
        "category_id": category_id,
        "price_range": {"min": min_price, "max": max_price} if min_price or max_price else None,
        "in_stock": in_stock,
        "location": {"lat": location_lat, "lng": location_lng, "radius_km": radius_km} if location_lat and location_lng else None,
        "sort": {"by": sort_by, "order": sort_order}
    }
    
    return SearchResponse(
        results=search_results,
        total=total,
        query=q,
        filters_applied=filters_applied,
        search_time_ms=search_time_ms,
        suggestions=suggestions
    )


@router.get("/recommendations", response_model=RecommendationResponse)
async def get_recommendations(
    user_id: Optional[int] = Query(None),
    product_id: Optional[int] = Query(None),
    category_id: Optional[int] = Query(None),
    recommendation_type: str = Query("personalized", regex="^(personalized|similar|collaborative|category)$"),
    limit: int = Query(10, ge=1, le=50),
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get product recommendations"""
    service = RecommendationService(db)
    
    # Use current user if not specified
    if not user_id and current_user:
        user_id = current_user.id
    
    recommendations = []
    based_on = {}
    
    if recommendation_type == "personalized" and user_id:
        recommendations = await service.get_personalized_recommendations(user_id, limit)
        based_on = {"user_id": user_id, "type": "personalized"}
    
    elif recommendation_type == "similar" and product_id:
        recommendations = await service.get_content_based_recommendations(product_id, limit)
        based_on = {"product_id": product_id, "type": "content_based"}
    
    elif recommendation_type == "collaborative" and user_id:
        recommendations = await service.get_collaborative_recommendations(user_id, limit)
        based_on = {"user_id": user_id, "type": "collaborative_filtering"}
    
    elif recommendation_type == "category" and category_id:
        recommendations = await service.get_category_recommendations(category_id, limit)
        based_on = {"category_id": category_id, "type": "category_popular"}
    
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid recommendation parameters"
        )
    
    # Convert to response format
    products_response = []
    for item in recommendations:
        product = item['product']
        
        # Get primary image
        primary_image = None
        if product.images:
            primary_img = next((img for img in product.images if img.is_primary), None)
            primary_image = primary_img.url if primary_img else product.images[0].url
        
        product_response = ProductListResponse(
            id=product.id,
            name=product.name,
            price=product.price,
            stock_quantity=product.stock_quantity,
            status=product.status,
            is_featured=product.is_featured,
            view_count=product.view_count,
            primary_image=primary_image,
            created_at=product.created_at
        )
        products_response.append(product_response)
    
    return RecommendationResponse(
        products=products_response,
        recommendation_type=recommendation_type,
        based_on=based_on,
        total=len(products_response)
    )


@router.get("/trending", response_model=TrendingProductsResponse)
async def get_trending_products(
    period: str = Query("week", regex="^(day|week|month)$"),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """Get trending products"""
    service = RecommendationService(db)
    
    # Map period to days
    period_days = {"day": 1, "week": 7, "month": 30}[period]
    
    recommendations = await service.get_trending_products(period_days, limit)
    
    # Convert to response format
    products_response = []
    for item in recommendations:
        product = item['product']
        
        # Get primary image
        primary_image = None
        if product.images:
            primary_img = next((img for img in product.images if img.is_primary), None)
            primary_image = primary_img.url if primary_img else product.images[0].url
        
        product_response = ProductListResponse(
            id=product.id,
            name=product.name,
            price=product.price,
            stock_quantity=product.stock_quantity,
            status=product.status,
            is_featured=product.is_featured,
            view_count=product.view_count,
            primary_image=primary_image,
            created_at=product.created_at
        )
        products_response.append(product_response)
    
    return TrendingProductsResponse(
        products=products_response,
        period=period,
        total=len(products_response)
    )


@router.get("/suggestions")
async def get_search_suggestions(
    q: str = Query(..., min_length=2, max_length=100),
    limit: int = Query(5, ge=1, le=10),
    db: AsyncSession = Depends(get_db)
):
    """Get search suggestions"""
    service = SearchService(db)
    suggestions = await service.get_search_suggestions(q, limit)
    
    return {"suggestions": suggestions}
