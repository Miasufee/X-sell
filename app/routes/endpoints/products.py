from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from app.core.database import get_db
from app.services.product import ProductService
from app.services.shop import ShopService
from app.schemas.product import (
    ProductCreate, ProductUpdate, ProductResponse, ProductListResponse, 
    ProductFilter, ProductImageResponse
)
from app.api.dependencies import get_current_user, get_current_merchant
from app.models.user import User

router = APIRouter()


@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    product_data: ProductCreate,
    current_user: User = Depends(get_current_merchant),
    db: AsyncSession = Depends(get_db)
):
    """Create a new product"""
    service = ProductService(db)
    product = await service.create_product(product_data, current_user)
    return ProductResponse.model_validate(product)


@router.get("/", response_model=List[ProductListResponse])
async def list_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    category_id: Optional[int] = Query(None),
    shop_id: Optional[int] = Query(None),
    merchant_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    is_featured: Optional[bool] = Query(None),
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    in_stock: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    sort_by: str = Query("created_at", regex="^(created_at|name|price|view_count)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    db: AsyncSession = Depends(get_db)
):
    """Get list of products with filtering and pagination"""
    filters = ProductFilter(
        category_id=category_id,
        shop_id=shop_id,
        merchant_id=merchant_id,
        status=status,
        is_featured=is_featured,
        min_price=min_price,
        max_price=max_price,
        in_stock=in_stock,
        search=search
    )
    
    service = ProductService(db)
    products, total = await service.get_products(filters, skip, limit, sort_by, sort_order)
    
    # Convert to list response format
    product_list = []
    for product in products:
        primary_image = None
        if product.images:
            primary_img = next((img for img in product.images if img.is_primary), None)
            primary_image = primary_img.url if primary_img else product.images[0].url
        
        product_list.append(ProductListResponse(
            id=product.id,
            name=product.name,
            price=product.price,
            stock_quantity=product.stock_quantity,
            status=product.status,
            is_featured=product.is_featured,
            view_count=product.view_count,
            primary_image=primary_image,
            created_at=product.created_at
        ))
    
    return product_list


@router.get("/nearby")
async def nearby_products(
    lat: float = Query(..., description="Latitude", ge=-90, le=90),
    lng: float = Query(..., description="Longitude", ge=-180, le=180),
    radius_km: int = Query(10, description="Search radius in kilometers", ge=1, le=50),
    category_id: Optional[int] = Query(None, description="Filter by category"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """Get products near a location"""
    shop_service = ShopService(db)
    products_with_distance, total = await shop_service.find_nearby_products(
        lat, lng, radius_km, skip, limit, category_id
    )
    
    # Convert to response format
    products_response = []
    for item in products_with_distance:
        product = item['product']
        shop = item['shop']
        distance = item['distance_km']
        
        # Get primary image
        primary_image = None
        if product.images:
            primary_img = next((img for img in product.images if img.is_primary), None)
            primary_image = primary_img.url if primary_img else product.images[0].url
        
        product_data = {
            "id": product.id,
            "name": product.name,
            "price": product.price,
            "stock_quantity": product.stock_quantity,
            "status": product.status,
            "is_featured": product.is_featured,
            "view_count": product.view_count,
            "primary_image": primary_image,
            "created_at": product.created_at,
            "shop": {
                "id": shop.id,
                "name": shop.name,
                "address": shop.address,
                "distance_km": distance
            }
        }
        products_response.append(product_data)
    
    return {
        "products": products_response,
        "total": total,
        "search_location": {"latitude": lat, "longitude": lng},
        "radius_km": radius_km
    }


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: int,
    increment_views: bool = Query(True, description="Whether to increment view count"),
    db: AsyncSession = Depends(get_db)
):
    """Get product by ID"""
    service = ProductService(db)
    product = await service.get_product(product_id, increment_views)
    return ProductResponse.model_validate(product)


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int,
    product_data: ProductUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update product"""
    service = ProductService(db)
    product = await service.update_product(product_id, product_data, current_user)
    return ProductResponse.model_validate(product)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete product"""
    service = ProductService(db)
    await service.delete_product(product_id, current_user)


@router.post("/{product_id}/images", response_model=ProductImageResponse, status_code=status.HTTP_201_CREATED)
async def upload_product_image(
    product_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Upload product image"""
    service = ProductService(db)
    image = await service.upload_product_image(product_id, file, current_user)
    return ProductImageResponse.model_validate(image)


@router.get("/{product_id}/images", response_model=List[ProductImageResponse])
async def get_product_images(
    product_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get all images for a product"""
    service = ProductService(db)
    images = await service.get_product_images(product_id)
    return [ProductImageResponse.model_validate(img) for img in images]


@router.delete("/{product_id}/images/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product_image(
    product_id: int,
    image_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete product image"""
    service = ProductService(db)
    await service.delete_product_image(product_id, image_id, current_user)


@router.get("/merchant/{merchant_id}", response_model=List[ProductListResponse])
async def get_merchant_products(
    merchant_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """Get products by merchant"""
    service = ProductService(db)
    products, total = await service.get_merchant_products(merchant_id, skip, limit)
    
    # Convert to list response format
    product_list = []
    for product in products:
        primary_image = None
        if product.images:
            primary_img = next((img for img in product.images if img.is_primary), None)
            primary_image = primary_img.url if primary_img else product.images[0].url
        
        product_list.append(ProductListResponse(
            id=product.id,
            name=product.name,
            price=product.price,
            stock_quantity=product.stock_quantity,
            status=product.status,
            is_featured=product.is_featured,
            view_count=product.view_count,
            primary_image=primary_image,
            created_at=product.created_at
        ))
    
    return product_list
