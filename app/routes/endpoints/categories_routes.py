# app/routes/category_schema.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.core.database import get_async_db
from app.schemas.category_schema import (
    CategoryCreate,
    CategoryResponse,
    CategoryUpdate,
    CategoryWithChildrenResponse,
    SubCategoryCreate,
    SubCategoryResponse,
    SubCategoryWithCategoryResponse,
    CategoryTreeResponse,
    CategorySearch,
    SubCategorySearch,
    CategoryStats,
    SubCategoryStats,
    PaginatedResponse
)
from app.crud.category_crud import CategoryService, SubCategoryService
from app.core.dependencies import CurrentUser, AdminUser

router = APIRouter(prefix="/categories", tags=["categories"])


# Category Routes
@router.post("/", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
        category_data: CategoryCreate,
        db: AsyncSession = Depends(get_async_db),
        admin_user: AdminUser = Depends()
):
    """Create a new category (Admin only)."""
    service = CategoryService()
    try:
        return await service.create_category(db, **category_data.model_dump())
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/", response_model=List[CategoryResponse])
async def get_categories(
        active_only: bool = True,
        include_children: bool = False,
        db: AsyncSession = Depends(get_async_db)
):
    """Get all categories."""
    service = CategoryService()
    return await service.get_active_categories(db, include_children, 0, 1000)


@router.get("/tree", response_model=CategoryTreeResponse)
async def get_category_tree(
        db: AsyncSession = Depends(get_async_db)
):
    """Get complete category hierarchy."""
    service = CategoryService()
    categories = await service.get_category_tree(db)
    return {"categories": categories}


@router.get("/{category_id}", response_model=CategoryWithChildrenResponse)
async def get_category(
        category_id: int,
        db: AsyncSession = Depends(get_async_db)
):
    """Get specific category with children."""
    service = CategoryService()
    category = await service.get_category_with_children(db, category_id)
    if not category or not category.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )

    # Get subcategories for this category
    subcategory_service = SubCategoryService()
    category.subcategories = await subcategory_service.get_category_subcategories(db, category_id)

    return category


@router.get("/slug/{slug}", response_model=CategoryWithChildrenResponse)
async def get_category_by_slug(
        slug: str,
        db: AsyncSession = Depends(get_async_db)
):
    """Get category by slug."""
    service = CategoryService()
    category = await service.get_by_slug(db, slug)
    if not category or not category.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )

    category.children = await service.get_category_children(db, category.id)

    # Get subcategories for this category
    subcategory_service = SubCategoryService()
    category.subcategories = await subcategory_service.get_category_subcategories(db, category.id)

    return category


@router.put("/{category_id}", response_model=CategoryResponse)
async def update_category(
        category_id: int,
        category_data: CategoryUpdate,
        db: AsyncSession = Depends(get_async_db),
        admin_user: AdminUser = Depends()
):
    """Update category (Admin only)."""
    service = CategoryService()
    try:
        category = await service.update_category(db, category_id, **category_data.model_dump(exclude_unset=True))
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found"
            )
        return category
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.patch("/{category_id}/toggle-status", response_model=CategoryResponse)
async def toggle_category_status(
        category_id: int,
        db: AsyncSession = Depends(get_async_db),
        admin_user: AdminUser = Depends()
):
    """Toggle category active status (Admin only)."""
    service = CategoryService()
    category = await service.toggle_category_status(db, category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    return category


@router.get("/search/categories", response_model=PaginatedResponse[CategoryResponse])
async def search_categories(
        search_params: CategorySearch = Depends(),
        db: AsyncSession = Depends(get_async_db)
):
    """Search categories with pagination."""
    service = CategoryService()
    skip = (search_params.page - 1) * search_params.per_page

    categories = await service.search_categories(
        db,
        search_term=search_params.search_term,
        active_only=search_params.active_only,
        skip=skip,
        limit=search_params.per_page
    )

    total = await service.count(db, filters={"is_active": True} if search_params.active_only else {})

    return {
        "items": categories,
        "total": total,
        "page": search_params.page,
        "per_page": search_params.per_page,
        "total_pages": (total + search_params.per_page - 1) // search_params.per_page,
        "has_next": search_params.page * search_params.per_page < total,
        "has_prev": search_params.page > 1
    }


@router.get("/stats/categories", response_model=CategoryStats)
async def get_category_stats(
        db: AsyncSession = Depends(get_async_db)
):
    """Get category statistics."""
    service = CategoryService()
    return await service.get_category_stats(db)


# SubCategory Routes
@router.post("/subcategories", response_model=SubCategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_subcategory(
        subcategory_data: SubCategoryCreate,
        db: AsyncSession = Depends(get_async_db),
        admin_user: AdminUser = Depends()
):
    """Create a new subcategory (Admin only)."""
    service = SubCategoryService()
    try:
        return await service.create_subcategory(db, **subcategory_data.model_dump())
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{category_id}/subcategories", response_model=List[SubCategoryResponse])
async def get_category_subcategories(
        category_id: int,
        active_only: bool = True,
        db: AsyncSession = Depends(get_async_db)
):
    """Get all subcategories for a specific category."""
    service = SubCategoryService()
    return await service.get_category_subcategories(db, category_id, active_only, 0, 1000)


@router.get("/subcategories/{subcategory_id}", response_model=SubCategoryWithCategoryResponse)
async def get_subcategory(
        subcategory_id: int,
        db: AsyncSession = Depends(get_async_db)
):
    """Get specific subcategory with category information."""
    service = SubCategoryService()
    subcategory = await service.get_subcategory_with_category(db, subcategory_id)
    if not subcategory or not subcategory.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subcategory not found"
        )
    return subcategory


@router.put("/subcategories/{subcategory_id}", response_model=SubCategoryResponse)
async def update_subcategory(
        subcategory_id: int,
        subcategory_data: SubCategoryUpdate,
        db: AsyncSession = Depends(get_async_db),
        admin_user: AdminUser = Depends()
):
    """Update subcategory (Admin only)."""
    service = SubCategoryService()
    try:
        subcategory = await service.update_subcategory(db, subcategory_id,
                                                       **subcategory_data.model_dump(exclude_unset=True))
        if not subcategory:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subcategory not found"
            )
        return subcategory
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.patch("/subcategories/{subcategory_id}/toggle-status", response_model=SubCategoryResponse)
async def toggle_subcategory_status(
        subcategory_id: int,
        db: AsyncSession = Depends(get_async_db),
        admin_user: AdminUser = Depends()
):
    """Toggle subcategory active status (Admin only)."""
    service = SubCategoryService()
    subcategory = await service.toggle_subcategory_status(db, subcategory_id)
    if not subcategory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subcategory not found"
        )
    return subcategory


@router.get("/search/subcategories", response_model=PaginatedResponse[SubCategoryResponse])
async def search_subcategories(
        search_params: SubCategorySearch = Depends(),
        db: AsyncSession = Depends(get_async_db)
):
    """Search subcategories with pagination."""
    service = SubCategoryService()
    skip = (search_params.page - 1) * search_params.per_page

    subcategories = await service.search_subcategories(
        db,
        search_term=search_params.search_term,
        category_id=search_params.category_id,
        active_only=search_params.active_only,
        skip=skip,
        limit=search_params.per_page
    )

    total = await service.count(db, filters={"is_active": True} if search_params.active_only else {})

    return {
        "items": subcategories,
        "total": total,
        "page": search_params.page,
        "per_page": search_params.per_page,
        "total_pages": (total + search_params.per_page - 1) // search_params.per_page,
        "has_next": search_params.page * search_params.per_page < total,
        "has_prev": search_params.page > 1
    }


@router.get("/stats/subcategories", response_model=SubCategoryStats)
async def get_subcategory_stats(
        category_id: Optional[int] = None,
        db: AsyncSession = Depends(get_async_db)
):
    """Get subcategory statistics."""
    service = SubCategoryService()
    return await service.get_subcategory_stats(db, category_id)