from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, or_, select
from typing import Optional, Dict, Any, Sequence
from .crud_base import CrudBase
from app.models import Category, SubCategory


class CategoryService(CrudBase[Category]):
    """Service for handling category operations."""

    def __init__(self):
        super().__init__(Category)

    async def create_category(
            self,
            db: AsyncSession,
            name: str,
            slug: str,
            description: Optional[str] = None,
            parent_id: Optional[int] = None,
            is_active: bool = True
    ) -> Category:
        """Create a new category."""
        # Check if slug already exists
        existing = await self.get_by_slug(db, slug)
        if existing:
            raise ValueError("Category with this slug already exists")

        category_data = {
            "name": name,
            "slug": slug,
            "description": description,
            "parent_id": parent_id,
            "is_active": is_active
        }

        return await self.create(db, **category_data)

    async def get_by_slug(
            self,
            db: AsyncSession,
            slug: str
    ) -> Optional[Category]:
        """Get category by slug."""
        return await self.get(db, filters={"slug": slug})

    async def get_active_categories(
            self,
            db: AsyncSession,
            include_children: bool = False,
            skip: int = 0,
            limit: int = 100
    ) -> Sequence[Category]:
        """Get all active categories."""
        categories = await self.get_multi(
            db,
            skip=skip,
            limit=limit,
            filters={"is_active": True},
            order_by="name"
        )

        if include_children:
            # Eager load children for each category
            for category in categories:
                category.children = await self.get_category_children(db, category.id)

        return categories

    async def get_category_tree(
            self,
            db: AsyncSession
    ) -> Sequence[Category]:
        """Get complete category hierarchy."""
        # Get all top-level categories (no parent)
        top_level_categories = await self.get_multi(
            db,
            filters={"parent_id": None, "is_active": True},
            order_by="name"
        )

        # Recursively load children for each top-level category
        for category in top_level_categories:
            category.children = await self._get_category_children_recursive(db, category.id)

        return top_level_categories

    async def _get_category_children_recursive(
            self,
            db: AsyncSession,
            category_id: int
    ) -> Sequence[Category]:
        """Recursively get all children of a category."""
        children = await self.get_multi(
            db,
            filters={"parent_id": category_id, "is_active": True},
            order_by="name"
        )

        for child in children:
            child.children = await self._get_category_children_recursive(db, child.id)

        return children

    async def get_category_children(
            self,
            db: AsyncSession,
            category_id: int
    ) -> Sequence[Category]:
        """Get direct children of a category."""
        return await self.get_multi(
            db,
            filters={"parent_id": category_id, "is_active": True},
            order_by="name"
        )

    async def get_category_with_children(
            self,
            db: AsyncSession,
            category_id: int
    ) -> Optional[Category]:
        """Get category with its direct children."""
        category = await self.get(db, obj_id=category_id)
        if category:
            category.children = await self.get_category_children(db, category_id)
        return category

    async def update_category(
            self,
            db: AsyncSession,
            category_id: int,
            **update_data
    ) -> Optional[Category]:
        """Update category with validation."""
        if "slug" in update_data:
            # Check if new slug is already taken by another category
            existing = await self.get(db, filters={"slug": update_data["slug"]})
            if existing and existing.id != category_id:
                raise ValueError("Category with this slug already exists")

        return await self.update(db, obj_id=category_id, **update_data)

    async def toggle_category_status(
            self,
            db: AsyncSession,
            category_id: int
    ) -> Optional[Category]:
        """Toggle category active status."""
        category = await self.get(db, obj_id=category_id)
        if not category:
            return None

        new_status = not category.is_active
        return await self.update(db, obj_id=category_id, is_active=new_status)

    async def search_categories(
            self,
            db: AsyncSession,
            search_term: Optional[str] = None,
            active_only: bool = True,
            skip: int = 0,
            limit: int = 100
    ) -> Sequence[Category]:
        """Search categories with text search."""
        conditions = []

        if active_only:
            conditions.append(Category.is_active == True)

        if search_term:
            search_condition = or_(
                Category.name.ilike(f"%{search_term}%"),
                Category.description.ilike(f"%{search_term}%"),
                Category.slug.ilike(f"%{search_term}%")
            )
            conditions.append(search_condition)

        where_clause = and_(*conditions) if conditions else None

        return await self.get_multi(
            db,
            skip=skip,
            limit=limit,
            where_clause=where_clause,
            order_by="name"
        )

    async def get_category_stats(
            self,
            db: AsyncSession
    ) -> Dict[str, Any]:
        """Get category statistics."""
        stats = {}

        # Total categories
        stats["total_categories"] = await self.count(db)
        stats["active_categories"] = await self.count(db, filters={"is_active": True})

        # Count top-level categories
        stats["top_level_categories"] = await self.count(db, filters={"parent_id": None, "is_active": True})

        return stats


class SubCategoryService(CrudBase[SubCategory]):
    """Service for handling subcategory operations."""

    def __init__(self):
        super().__init__(SubCategory)

    async def create_subcategory(
            self,
            db: AsyncSession,
            category_id: int,
            name: str,
            slug: str,
            description: Optional[str] = None,
            is_active: bool = True
    ) -> SubCategory:
        """Create a new subcategory."""
        # Check if slug already exists for this category
        existing = await self.get_by_slug(db, category_id, slug)
        if existing:
            raise ValueError("Subcategory with this slug already exists for this category")

        subcategory_data = {
            "category_id": category_id,
            "name": name,
            "slug": slug,
            "description": description,
            "is_active": is_active
        }

        return await self.create(db, **subcategory_data)

    async def get_by_slug(
            self,
            db: AsyncSession,
            category_id: int,
            slug: str
    ) -> Optional[SubCategory]:
        """Get subcategory by slug within a category."""
        return await self.get(db, filters={"category_id": category_id, "slug": slug})

    async def get_category_subcategories(
            self,
            db: AsyncSession,
            category_id: int,
            active_only: bool = True,
            skip: int = 0,
            limit: int = 100
    ) -> Sequence[SubCategory]:
        """Get all subcategories for a specific category."""
        filters = {"category_id": category_id}
        if active_only:
            filters["is_active"] = True

        return await self.get_multi(
            db,
            skip=skip,
            limit=limit,
            filters=filters,
            order_by="name"
        )

    async def get_subcategory_with_category(
            self,
            db: AsyncSession,
            subcategory_id: int
    ) -> Optional[SubCategory]:
        """Get subcategory with category information."""
        from sqlalchemy.orm import joinedload

        stmt = select(SubCategory).options(
            joinedload(SubCategory.category)
        ).where(SubCategory.id.is_(subcategory_id))

        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def update_subcategory(
            self,
            db: AsyncSession,
            subcategory_id: int,
            **update_data
    ) -> Optional[SubCategory]:
        """Update subcategory with validation."""
        if "slug" in update_data:
            subcategory = await self.get(db, obj_id=subcategory_id)
            if subcategory:
                # Check if new slug is already taken by another subcategory in same category
                existing = await self.get(
                    db,
                    filters={
                        "category_id": subcategory.category_id,
                        "slug": update_data["slug"]
                    }
                )
                if existing and existing.id != subcategory_id:
                    raise ValueError("Subcategory with this slug already exists for this category")

        return await self.update(db, obj_id=subcategory_id, **update_data)

    async def toggle_subcategory_status(
            self,
            db: AsyncSession,
            subcategory_id: int
    ) -> Optional[SubCategory]:
        """Toggle subcategory active status."""
        subcategory = await self.get(db, obj_id=subcategory_id)
        if not subcategory:
            return None

        new_status = not subcategory.is_active
        return await self.update(db, obj_id=subcategory_id, is_active=new_status)

    async def search_subcategories(
            self,
            db: AsyncSession,
            search_term: Optional[str] = None,
            category_id: Optional[int] = None,
            active_only: bool = True,
            skip: int = 0,
            limit: int = 100
    ) -> Sequence[SubCategory]:
        """Search subcategories with various filters."""
        conditions = []

        if active_only:
            conditions.append(SubCategory.is_active == True)

        if category_id:
            conditions.append(SubCategory.category_id == category_id)

        if search_term:
            search_condition = or_(
                SubCategory.name.ilike(f"%{search_term}%"),
                SubCategory.description.ilike(f"%{search_term}%"),
                SubCategory.slug.ilike(f"%{search_term}%")
            )
            conditions.append(search_condition)

        where_clause = and_(*conditions) if conditions else None

        return await self.get_multi(
            db,
            skip=skip,
            limit=limit,
            where_clause=where_clause,
            order_by="name"
        )

    async def get_subcategory_stats(
            self,
            db: AsyncSession,
            category_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get subcategory statistics."""
        stats = {}
        filters = {}

        if category_id:
            filters["category_id"] = category_id

        # Total subcategories
        stats["total_subcategories"] = await self.count(db, filters=filters)
        stats["active_subcategories"] = await self.count(
            db,
            filters={**filters, "is_active": True}
        )

        return stats