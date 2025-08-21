from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, update, delete
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from typing import Generic, TypeVar, Optional, Type, Any, List, Dict
import logging

ModelType = TypeVar('ModelType')
logger = logging.getLogger(__name__)


class CrudBase(Generic[ModelType]):
    """Simplified CRUD base class for SQLAlchemy async operations."""

    def __init__(self, model: Type[ModelType]):
        self.model = model

    @staticmethod
    async def _handle_db_operation(db: AsyncSession, operation, is_write: bool = False):
        """Unified error handling for database operations."""
        try:
            result = await operation()
            if is_write:
                await db.commit()
            return result
        except (IntegrityError, SQLAlchemyError) as e:
            if is_write:
                await db.rollback()
            logger.error(f"Database error: {e}")
            raise
        except Exception as e:
            if is_write:
                await db.rollback()
            logger.error(f"Unexpected error: {e}")
            raise

    def _build_filters(self, filters: Optional[Dict[str, Any]] = None, **kwargs):
        """Build filter conditions from dict and kwargs."""
        conditions = []
        all_filters = {**(filters or {}), **kwargs}

        for field, value in all_filters.items():
            if hasattr(self.model, field):
                column = getattr(self.model, field)
                if isinstance(value, (list, tuple)):
                    conditions.append(column.in_(value))
                else:
                    conditions.append(column == value)

        return conditions

    # CREATE Operations
    async def create(self, db: AsyncSession, **data) -> ModelType:
        """Create a new record."""

        async def _op():
            obj = self.model(**data)
            db.add(obj)
            await db.flush()
            await db.refresh(obj)
            return obj

        return await self._handle_db_operation(db, _op, is_write=True)

    async def create_many(self, db: AsyncSession, objects: List[Dict[str, Any]]) -> List[ModelType]:
        """Create multiple records."""

        async def _op():
            db_objects = [self.model(**obj) for obj in objects]
            db.add_all(db_objects)
            await db.flush()
            return db_objects

        return await self._handle_db_operation(db, _op, is_write=True)

    # READ Operations
    async def get_by_id(self, db: AsyncSession, obj_id: Any) -> Optional[ModelType]:
        """Get a single record by ID."""

        async def _op():
            return await db.get(self.model, obj_id)

        return await self._handle_db_operation(db, _op)

    async def get_one(self, db: AsyncSession, filters: Optional[Dict[str, Any]] = None, **kwargs) -> Optional[
        ModelType]:
        """Get a single record by filters."""

        async def _op():
            stmt = select(self.model)
            conditions = self._build_filters(filters, **kwargs)

            if conditions:
                stmt = stmt.where(and_(*conditions))

            result = await db.execute(stmt)
            return result.scalars().first()

        return await self._handle_db_operation(db, _op)

    async def get_many(
            self,
            db: AsyncSession,
            skip: int = 0,
            limit: int = 100,
            filters: Optional[Dict[str, Any]] = None,
            order_by: Optional[Any] = None,
            **kwargs
    ) -> List[ModelType]:
        """Get multiple records with pagination."""

        async def _op():
            stmt = select(self.model)
            conditions = self._build_filters(filters, **kwargs)

            if conditions:
                stmt = stmt.where(and_(*conditions))

            if order_by is not None:
                stmt = stmt.order_by(order_by)

            stmt = stmt.offset(skip).limit(limit)
            result = await db.execute(stmt)
            return result.scalars().all()

        return await self._handle_db_operation(db, _op)

    async def count(self, db: AsyncSession, filters: Optional[Dict[str, Any]] = None, **kwargs) -> int:
        """Count records matching filters."""

        async def _op():
            stmt = select(func.count()).select_from(self.model)
            conditions = self._build_filters(filters, **kwargs)

            if conditions:
                stmt = stmt.where(and_(*conditions))

            result = await db.execute(stmt)
            return result.scalar_one()

        return await self._handle_db_operation(db, _op)

    async def exists(self, db: AsyncSession, filters: Optional[Dict[str, Any]] = None, **kwargs) -> bool:
        """Check if records exist matching filters."""

        async def _op():
            stmt = select(1).select_from(self.model).limit(1)
            conditions = self._build_filters(filters, **kwargs)

            if conditions:
                stmt = stmt.where(and_(*conditions))

            result = await db.execute(stmt)
            return result.scalar() is not None

        return await self._handle_db_operation(db, _op)

    # UPDATE Operations
    async def update_by_id(self, db: AsyncSession, obj_id: Any, **data) -> Optional[ModelType]:
        """Update a record by ID."""

        async def _op():
            obj = await db.get(self.model, obj_id)
            if not obj:
                return None

            for key, value in data.items():
                if hasattr(obj, key):
                    setattr(obj, key, value)

            await db.flush()
            await db.refresh(obj)
            return obj

        return await self._handle_db_operation(db, _op, is_write=True)

    async def update_many(
            self,
            db: AsyncSession,
            update_data: Dict[str, Any],
            filters: Optional[Dict[str, Any]] = None,
            **kwargs
    ) -> int:
        """Update multiple records."""

        async def _op():
            stmt = update(self.model).values(**update_data)
            conditions = self._build_filters(filters, **kwargs)

            if conditions:
                stmt = stmt.where(and_(*conditions))

            result = await db.execute(stmt)
            return result.rowcount

        return await self._handle_db_operation(db, _op, is_write=True)

    # DELETE Operations
    async def delete_by_id(self, db: AsyncSession, obj_id: Any) -> bool:
        """Delete a record by ID."""

        async def _op():
            obj = await db.get(self.model, obj_id)
            if not obj:
                return False

            await db.delete(obj)
            return True

        return await self._handle_db_operation(db, _op, is_write=True)

    async def delete_many(
            self,
            db: AsyncSession,
            filters: Optional[Dict[str, Any]] = None,
            **kwargs
    ) -> int:
        """Delete multiple records."""
        if not filters and not kwargs:
            raise ValueError("Must provide filters to prevent accidental deletion of all records")

        async def _op():
            stmt = delete(self.model)
            conditions = self._build_filters(filters, **kwargs)

            if conditions:
                stmt = stmt.where(and_(*conditions))

            result = await db.execute(stmt)
            return result.rowcount

        return await self._handle_db_operation(db, _op, is_write=True)

    # UTILITY Operations
    async def paginate(
            self,
            db: AsyncSession,
            page: int = 1,
            per_page: int = 20,
            filters: Optional[Dict[str, Any]] = None,
            order_by: Optional[Any] = None,
            **kwargs
    ) -> Dict[str, Any]:
        """Get paginated results with metadata."""

        async def _op():
            skip = (page - 1) * per_page

            # Get total count and items in parallel
            total = await self.count(db, filters=filters, **kwargs)
            items = await self.get_many(
                db,
                skip=skip,
                limit=per_page,
                filters=filters,
                order_by=order_by,
                **kwargs
            )

            return {
                "items": items,
                "total": total,
                "page": page,
                "per_page": per_page,
                "total_pages": (total + per_page - 1) // per_page,
                "has_next": page * per_page < total,
                "has_prev": page > 1
            }

        return await self._handle_db_operation(db, _op)
