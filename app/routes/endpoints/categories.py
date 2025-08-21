from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.core.database import get_db
from app.crud.category import CategoryRepository
from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryResponse
from app.api.dependencies import get_current_admin
from app.models.user import User

router = APIRouter()


@router.post("/", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    category_data: CategoryCreate,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Create a new category (admin only)"""
    repo = CategoryRepository(db)
    
    # Check if slug already exists
    existing_category = await repo.get_by_slug(category_data.slug)
    if existing_category:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category slug already exists"
        )
    
    category = await repo.create(category_data)
    return CategoryResponse.model_validate(category)


@router.get("/", response_model=List[CategoryResponse])
async def list_categories(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    active_only: bool = Query(True),
    db: AsyncSession = Depends(get_db)
):
    """Get list of categories"""
    repo = CategoryRepository(db)
    categories, total = await repo.get_list(skip, limit, active_only)
    return [CategoryResponse.model_validate(cat) for cat in categories]


@router.get("/{category_id}", response_model=CategoryResponse)
async def get_category(
    category_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get category by ID"""
    repo = CategoryRepository(db)
    category = await repo.get_by_id(category_id)
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    return CategoryResponse.model_validate(category)


@router.put("/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: int,
    category_data: CategoryUpdate,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Update category (admin only)"""
    repo = CategoryRepository(db)
    category = await repo.get_by_id(category_id)
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    # Check slug uniqueness if being updated
    if category_data.slug and category_data.slug != category.slug:
        existing_category = await repo.get_by_slug(category_data.slug)
        if existing_category:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Category slug already exists"
            )
    
    updated_category = await repo.update(category, category_data)
    return CategoryResponse.model_validate(updated_category)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: int,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Delete category (admin only)"""
    repo = CategoryRepository(db)
    category = await repo.get_by_id(category_id)
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    await repo.delete(category)
