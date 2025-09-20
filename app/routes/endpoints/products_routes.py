from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db
from app.schemas import (
    ProductCreate,
    ProductResponse,
    ProductUpdate,
    ProductSearch,
    ProductStats,
    ProductImageCreate,
    ProductImageResponse,
    ProductVariantCreate,
    ProductVariantResponse,
    PaginatedResponse
)
from app.crud.product_crud import ProductService
from app.crud.merchant_crud import MerchantService
from app.core.dependencies import CurrentUser

router = APIRouter(prefix="/products", tags=["products"])


@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
        product_data: ProductCreate,
        db: AsyncSession = Depends(get_async_db),
        current_user: CurrentUser = Depends()
):
    """Create a new product (Merchant only)."""
    # Check if user is approved merchant
    merchant_service = MerchantService()
    application = await merchant_service.get_user_application(db, current_user.id)
    if not application or application.status != "approved":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You need to be an approved merchant to create products"
        )

    service = ProductService()
    return await service.create_product(db, current_user.id, **product_data.model_dump())


@router.get("/", response_model=PaginatedResponse[ProductResponse])
async def search_products(
        search_params: ProductSearch = Depends(),
        db: AsyncSession = Depends(get_async_db)
):
    """Search products with various filters."""
    service = ProductService()
    skip = (search_params.page - 1) * search_params.per_page

    products = await service.search_products(
        db,
        search_term=search_params.search_term,
        category_id=search_params.category_id,
        shop_id=search_params.shop_id,
        min_price=search_params.min_price,
        max_price=search_params.max_price,
        status=search_params.status or "active",
        featured_only=search_params.featured_only,
        skip=skip,
        limit=search_params.per_page
    )

    total = await service.count(db, filters={"status": "active"})

    return {
        "items": products,
        "total": total,
        "page": search_params.page,
        "per_page": search_params.per_page,
        "total_pages": (total + search_params.per_page - 1) // search_params.per_page,
        "has_next": search_params.page * search_params.per_page < total,
        "has_prev": search_params.page > 1
    }


@router.get("/featured", response_model=List[ProductResponse])
async def get_featured_products(
        limit: int = 20,
        db: AsyncSession = Depends(get_async_db)
):
    """Get featured products."""
    service = ProductService()
    return await service.get_featured_products(db, limit)


@router.get("/popular", response_model=List[ProductResponse])
async def get_popular_products(
        limit: int = 20,
        db: AsyncSession = Depends(get_async_db)
):
    """Get popular products."""
    service = ProductService()
    return await service.get_popular_products(db, limit)


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
        product_id: int,
        db: AsyncSession = Depends(get_async_db)
):
    """Get specific product details."""
    service = ProductService()
    product = await service.get(db, obj_id=product_id)
    if not product or product.status != "active":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    # Increment view count
    await service.increment_view_count(db, product_id)
    return product


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
        product_id: int,
        product_data: ProductUpdate,
        db: AsyncSession = Depends(get_async_db),
        current_user: CurrentUser = Depends()
):
    """Update product details (Product owner only)."""
    service = ProductService()
    product = await service.get(db, obj_id=product_id)
    if not product or product.merchant_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found or access denied"
        )

    return await service.update(db, obj_id=product_id, **product_data.model_dump(exclude_unset=True))


@router.patch("/{product_id}/status", response_model=ProductResponse)
async def update_product_status(
        product_id: int,
        status: str,
        db: AsyncSession = Depends(get_async_db),
        current_user: CurrentUser = Depends()
):
    """Update product status (Product owner only)."""
    service = ProductService()
    product = await service.update_product_status(db, product_id, current_user.id, status)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found or access denied"
        )
    return product


@router.patch("/{product_id}/toggle-featured", response_model=ProductResponse)
async def toggle_featured_status(
        product_id: int,
        db: AsyncSession = Depends(get_async_db),
        current_user: CurrentUser = Depends()
):
    """Toggle product featured status (Product owner only)."""
    service = ProductService()
    product = await service.toggle_featured_status(db, product_id, current_user.id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found or access denied"
        )
    return product


@router.post("/{product_id}/images", response_model=ProductImageResponse, status_code=status.HTTP_201_CREATED)
async def add_product_image(
        product_id: int,
        image_data: ProductImageCreate,
        db: AsyncSession = Depends(get_async_db),
        current_user: CurrentUser = Depends()
):
    """Add image to product (Product owner only)."""
    service = ProductService()
    image = await service.add_product_image(db, product_id, current_user.id, **image_data.model_dump())
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found or access denied"
        )
    return image


@router.post("/{product_id}/variants", response_model=ProductVariantResponse, status_code=status.HTTP_201_CREATED)
async def add_product_variant(
        product_id: int,
        variant_data: ProductVariantCreate,
        db: AsyncSession = Depends(get_async_db),
        current_user: CurrentUser = Depends()
):
    """Add variant to product (Product owner only)."""
    service = ProductService()
    variant = await service.create_product_variant(db, product_id, current_user.id, **variant_data.model_dump())
    if not variant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found or access denied"
        )
    return variant


@router.get("/stats/my-products", response_model=ProductStats)
async def get_my_product_stats(
        db: AsyncSession = Depends(get_async_db),
        current_user: CurrentUser = Depends()
):
    """Get current user's product statistics."""
    service = ProductService()
    return await service.get_product_stats(db, current_user.id)