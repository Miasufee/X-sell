from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, update, delete
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from typing import (
    Generic,
    TypeVar,
    Optional,
    Type,
    Any,
    Sequence,
    List,
    Dict,
    Union,
    Tuple,
)
import logging
from sqlalchemy.orm import load_only as sqlalchemy_load_only

ModelType = TypeVar('ModelType')
logger = logging.getLogger(__name__)


class CrudBase(Generic[ModelType]):
    def __init__(self, model: Type[ModelType]):
        """
        Initialize CRUD operations for a specific model.

        Args:
            model: SQLAlchemy model class
        """
        self.model = model

    # ============ HELPER METHODS ============

    def _build_filters(self, filters: Optional[Dict[str, Any]] = None, **kwargs) -> List[Any]:
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

    def _build_order_by(self, order_by: Optional[Any] = None) -> Optional[Any]:
        """Build proper order_by clause from various input formats."""
        if order_by is None:
            return None

        if isinstance(order_by, (list, tuple)):
            return self._build_order_by_list(order_by)
        elif isinstance(order_by, str):
            return self._build_order_by_str(order_by)
        else:
            # Assume it's already a proper SQLAlchemy expression
            return order_by

    def _build_order_by_list(self, order_by_list: List[Any]) -> List[Any]:
        """Build order_by from a list of items."""
        valid_order_by = []
        for item in order_by_list:
            if isinstance(item, str):
                order_expr = self._convert_string_to_order_expr(item)
                if order_expr is not None:
                    valid_order_by.append(order_expr)
            else:
                # Assume it's already a proper SQLAlchemy expression
                valid_order_by.append(item)
        return valid_order_by

    def _build_order_by_str(self, order_by_str: str) -> Optional[Any]:
        """Build order_by from a single string."""
        order_expr = self._convert_string_to_order_expr(order_by_str)
        return order_expr

    def _convert_string_to_order_expr(self, order_str: str) -> Optional[Any]:
        """Convert string to proper SQLAlchemy order expression."""
        if order_str.startswith('-'):
            column_name = order_str[1:]
            if hasattr(self.model, column_name):
                return getattr(self.model, column_name).desc()
            else:
                logger.warning(f"Invalid column name in order_by: {column_name}")
                return None
        else:
            if hasattr(self.model, order_str):
                return getattr(self.model, order_str).asc()
            else:
                logger.warning(f"Invalid column name in order_by: {order_str}")
                return None

    @staticmethod
    def _apply_load_only(stmt, load_only: Optional[List[str]] = None):
        """Apply load_only options to statement."""
        if load_only:
            stmt = stmt.options(sqlalchemy_load_only(*load_only))
        return stmt

    def _apply_filters(self, stmt, filters: Optional[Dict[str, Any]] = None, **kwargs):
        """Apply filter conditions to statement."""
        conditions = self._build_filters(filters, **kwargs)
        if conditions:
            stmt = stmt.where(and_(*conditions))
        return stmt

    @staticmethod
    def _apply_where_clause(stmt, where_clause: Optional[Any] = None):
        """Apply custom where clause to statement."""
        if where_clause is not None:
            stmt = stmt.where(where_clause)
        return stmt

    def _apply_order_by(self, stmt, order_by: Optional[Any] = None):
        """Apply order_by clause to statement."""
        order_by_clause = self._build_order_by(order_by)
        if order_by_clause:
            if isinstance(order_by_clause, (list, tuple)):
                stmt = stmt.order_by(*order_by_clause)
            else:
                stmt = stmt.order_by(order_by_clause)
        return stmt

    @staticmethod
    def _apply_pagination(stmt, skip: int = 0, limit: int = 100):
        """Apply pagination to statement."""
        return stmt.offset(skip).limit(limit)

    @staticmethod
    async def _execute_write_operation(db: AsyncSession, operation_name: str, db_operation):
        """Execute a database write operation with error handling and commit."""
        try:
            result = await db_operation()
            await db.commit()
            return result
        except IntegrityError as e:
            await db.rollback()
            logger.error(f"Integrity error during {operation_name}: {e}")
            raise
        except SQLAlchemyError as e:
            await db.rollback()
            logger.error(f"Database error during {operation_name}: {e}")
            raise
        except Exception as e:
            await db.rollback()
            logger.error(f"Unexpected error during {operation_name}: {e}")
            raise

    @staticmethod
    async def _execute_read_operation(db: AsyncSession, operation_name: str, db_operation):
        """Execute a database read operation with error handling."""
        try:
            return await db_operation()
        except SQLAlchemyError as e:
            logger.error(f"Database error during {operation_name}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during {operation_name}: {e}")
            raise

    # ============ MAIN CRUD METHODS ============

    # CREATE Operations
    async def create(self, db: AsyncSession, **kwargs: Any) -> ModelType:
        """Create a new record"""

        async def _op():
            db_obj = self.model(**kwargs)
            db.add(db_obj)
            await db.flush()
            await db.refresh(db_obj)
            return db_obj

        return await self._execute_write_operation(db, "create", _op)

    async def bulk_create(self, db: AsyncSession, objects: List[Dict[str, Any]]) -> List[ModelType]:
        """Bulk create records"""

        async def _op():
            db_objects = [self.model(**obj) for obj in objects]
            db.add_all(db_objects)
            await db.flush()
            for db_obj in db_objects:
                await db.refresh(db_obj)
            return db_objects

        return await self._execute_write_operation(db, "bulk_create", _op)

    # READ Operations
    async def get(
            self,
            db: AsyncSession,
            *,
            obj_id: Optional[Any] = None,
            filters: Optional[Dict[str, Any]] = None,
            columns: Optional[List[str]] = None,
            load_only: Optional[List[str]] = None,
            where_clause: Optional[Any] = None,
            **kwargs: Any
    ) -> Union[Optional[ModelType], Optional[Tuple]]:
        """Get a single record with flexible column selection"""

        async def _op():
            if obj_id is not None:
                kwargs['id'] = obj_id

            if columns:
                valid_columns = []
                for col in columns:
                    if hasattr(self.model, col):
                        valid_columns.append(getattr(self.model, col))
                    else:
                        logger.warning(f"Invalid column name: {col}")

                if not valid_columns:
                    raise ValueError("No valid columns specified")

                stmt = select(*valid_columns)
            elif load_only:
                stmt = select(self.model)
                stmt = self._apply_load_only(stmt, load_only)
            else:
                stmt = select(self.model)

            stmt = self._apply_filters(stmt, filters, **kwargs)
            stmt = self._apply_where_clause(stmt, where_clause)

            result = await db.execute(stmt)
            return result.first() if columns else result.scalars().first()

        return await self._execute_read_operation(db, "get", _op)

    async def get_multi(
            self,
            db: AsyncSession,
            *,
            skip: int = 0,
            limit: int = 100,
            filters: Optional[Dict[str, Any]] = None,
            order_by: Optional[Any] = None,
            load_only: Optional[List[str]] = None,
            where_clause: Optional[Any] = None,
            **kwargs: Any
    ) -> Sequence[ModelType]:
        """Get multiple records with pagination"""

        async def _op():
            stmt = select(self.model)
            stmt = self._apply_load_only(stmt, load_only)
            stmt = self._apply_filters(stmt, filters, **kwargs)
            stmt = self._apply_where_clause(stmt, where_clause)
            stmt = self._apply_order_by(stmt, order_by)
            stmt = self._apply_pagination(stmt, skip, limit)

            result = await db.execute(stmt)
            return result.scalars().all()

        return await self._execute_read_operation(db, "get_multi", _op)

    # UPDATE Operations
    async def update(
            self,
            db: AsyncSession,
            *,
            db_obj: Optional[ModelType] = None,
            obj_id: Optional[Any] = None,
            **kwargs: Any
    ) -> ModelType:
        """Update a record"""

        async def _op():
            nonlocal db_obj
            if db_obj is None and obj_id is not None:
                db_obj = await self.get(db, obj_id=obj_id)
                if not db_obj:
                    raise ValueError(f"Record with id {obj_id} not found")
            elif db_obj is None:
                raise ValueError("Either db_obj or obj_id must be provided")

            for key, value in kwargs.items():
                if hasattr(db_obj, key):
                    setattr(db_obj, key, value)
                else:
                    logger.warning(f"Attribute {key} does not exist on model {self.model.__name__}")

            await db.flush()
            await db.refresh(db_obj)
            return db_obj

        return await self._execute_write_operation(db, "update", _op)

    async def bulk_update(
            self,
            db: AsyncSession,
            *,
            filters: Optional[Dict[str, Any]] = None,
            update_values: Dict[str, Any],
            where_clause: Optional[Any] = None,
            **kwargs: Any
    ) -> int:
        """Bulk update records"""

        async def _op():
            stmt = update(self.model)
            stmt = self._apply_filters(stmt, filters, **kwargs)
            stmt = self._apply_where_clause(stmt, where_clause)
            stmt = stmt.values(**update_values)

            result = await db.execute(stmt)
            return result.rowcount

        return await self._execute_write_operation(db, "bulk_update", _op)

    # DELETE Operations
    async def delete(
            self,
            db: AsyncSession,
            *,
            db_obj: Optional[ModelType] = None,
            obj_id: Optional[Any] = None,
            filters: Optional[Dict[str, Any]] = None,
            where_clause: Optional[Any] = None,
            soft_delete: bool = False,
            **kwargs: Any
    ) -> Union[int, None]:
        """Delete records matching the criteria. Returns number of affected rows for bulk operations."""
        if not any([db_obj, obj_id, filters, where_clause, kwargs]):
            raise ValueError("Must provide at least one deletion criteria")

        async def _op():
            nonlocal db_obj
            if db_obj is not None:
                if soft_delete and hasattr(db_obj, 'is_deleted'):
                    db_obj.is_deleted = True
                    await db.flush()
                else:
                    await db.delete(db_obj)
                return None
            elif obj_id is not None:
                db_obj = await self.get(db, obj_id=obj_id)
                if not db_obj:
                    raise ValueError(f"Record with id {obj_id} not found")
                if soft_delete and hasattr(db_obj, 'is_deleted'):
                    db_obj.is_deleted = True
                    await db.flush()
                else:
                    await db.delete(db_obj)
                return None
            else:
                if soft_delete and hasattr(self.model, 'is_deleted'):
                    stmt = update(self.model).values(is_deleted=True)
                else:
                    stmt = delete(self.model)

                stmt = self._apply_filters(stmt, filters, **kwargs)
                stmt = self._apply_where_clause(stmt, where_clause)

                result = await db.execute(stmt)
                return result.rowcount

        return await self._execute_write_operation(db, "delete", _op)

    # UTILITY Operations
    async def count(
            self,
            db: AsyncSession,
            *,
            filters: Optional[Dict[str, Any]] = None,
            where_clause: Optional[Any] = None,
            **kwargs: Any
    ) -> int:
        """Count records matching filters"""

        async def _op():
            stmt = select(func.count()).select_from(self.model)
            stmt = self._apply_filters(stmt, filters, **kwargs)
            stmt = self._apply_where_clause(stmt, where_clause)

            result = await db.execute(stmt)
            return result.scalar_one()

        return await self._execute_read_operation(db, "count", _op)

    async def exists(
            self,
            db: AsyncSession,
            *,
            filters: Optional[Dict[str, Any]] = None,
            where_clause: Optional[Any] = None,
            **kwargs: Any
    ) -> bool:
        """Check if records exist matching filters"""

        async def _op():
            stmt = select(self.model.id).limit(1)
            stmt = self._apply_filters(stmt, filters, **kwargs)
            stmt = self._apply_where_clause(stmt, where_clause)

            result = await db.execute(stmt)
            return result.scalar() is not None

        return await self._execute_read_operation(db, "exists", _op)

    async def paginate(
            self,
            db: AsyncSession,
            *,
            page: int = 1,
            per_page: int = 20,
            filters: Optional[Dict[str, Any]] = None,
            order_by: Optional[Any] = None,
            where_clause: Optional[Any] = None,
            **kwargs: Any
    ) -> Dict[str, Any]:
        """Paginated results with metadata"""

        async def _op():
            if page < 1:
                raise ValueError("Page must be >= 1")
            if per_page < 1:
                raise ValueError("Per page must be >= 1")

            skip = (page - 1) * per_page

            total = await self.count(db, filters=filters, where_clause=where_clause, **kwargs)
            items = await self.get_multi(
                db,
                skip=skip,
                limit=per_page,
                filters=filters,
                order_by=order_by,
                where_clause=where_clause,
                **kwargs
            )

            total_pages = (total + per_page - 1) // per_page

            return {
                "items": items,
                "total": total,
                "page": page,
                "per_page": per_page,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1
            }

        return await self._execute_read_operation(db, "paginate", _op)

# from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy import select, and_, func, update, delete
# from sqlalchemy.exc import IntegrityError, SQLAlchemyError
# from typing import (
#     Generic,
#     TypeVar,
#     Optional,
#     Type,
#     Any,
#     Sequence,
#     List,
#     Dict,
#     Union,
#     Tuple,
# )
# import logging
# from sqlalchemy.orm import load_only as sqlalchemy_load_only
#
# ModelType = TypeVar('ModelType')
# logger = logging.getLogger(__name__)
#
#
# class CrudBase(Generic[ModelType]):
#     def __init__(self, model: Type[ModelType]):
#         """
#         Initialize CRUD operations for a specific model.
#
#         Args:
#             model: SQLAlchemy model class
#         """
#         self.model = model
#
#     def _build_filters(self, filters: Optional[Dict[str, Any]] = None, **kwargs) -> List[Any]:
#         """Build filter conditions from dict and kwargs."""
#         conditions = []
#         all_filters = {**(filters or {}), **kwargs}
#
#         for field, value in all_filters.items():
#             if hasattr(self.model, field):
#                 column = getattr(self.model, field)
#                 if isinstance(value, (list, tuple)):
#                     conditions.append(column.in_(value))
#                 else:
#                     conditions.append(column == value)
#
#         return conditions
#
#     @staticmethod
#     async def _execute_write_operation(db: AsyncSession, operation_name: str, db_operation):
#         """Execute a database write operation with error handling and commit."""
#         try:
#             result = await db_operation()
#             await db.commit()
#             return result
#         except IntegrityError as e:
#             await db.rollback()
#             logger.error(f"Integrity error during {operation_name}: {e}")
#             raise
#         except SQLAlchemyError as e:
#             await db.rollback()
#             logger.error(f"Database error during {operation_name}: {e}")
#             raise
#         except Exception as e:
#             await db.rollback()
#             logger.error(f"Unexpected error during {operation_name}: {e}")
#             raise
#
#     @staticmethod
#     async def _execute_read_operation(db: AsyncSession, operation_name: str, db_operation):
#         """Execute a database read operation with error handling."""
#         try:
#             return await db_operation()
#         except SQLAlchemyError as e:
#             logger.error(f"Database error during {operation_name}: {e}")
#             raise
#         except Exception as e:
#             logger.error(f"Unexpected error during {operation_name}: {e}")
#             raise
#
#     # CREATE Operations
#     async def create(self, db: AsyncSession, **kwargs: Any) -> ModelType:
#         """Create a new record"""
#
#         async def _op():
#             db_obj = self.model(**kwargs)
#             db.add(db_obj)
#             await db.flush()
#             await db.refresh(db_obj)
#             return db_obj
#
#         return await self._execute_write_operation(db, "create", _op)
#
#     async def bulk_create(self, db: AsyncSession, objects: List[Dict[str, Any]]) -> List[ModelType]:
#         """Bulk create records"""
#
#         async def _op():
#             db_objects = [self.model(**obj) for obj in objects]
#             db.add_all(db_objects)
#             await db.flush()
#             return db_objects
#
#         return await self._execute_write_operation(db, "bulk_create", _op)
#
#     # READ Operations
#     async def get(
#             self,
#             db: AsyncSession,
#             *,
#             obj_id: Optional[Any] = None,
#             filters: Optional[Dict[str, Any]] = None,
#             columns: Optional[List[str]] = None,
#             load_only: Optional[List[str]] = None,
#             where_clause: Optional[Any] = None,
#             **kwargs: Any
#     ) -> Union[Optional[ModelType], Optional[Tuple]]:
#         """Get a single record with flexible column selection"""
#
#         async def _op():
#             if obj_id is not None:
#                 kwargs['id'] = obj_id
#
#             if columns:
#                 selected = [getattr(self.model, col) for col in columns]
#                 stmt = select(*selected)
#             elif load_only:
#                 stmt = select(self.model).options(sqlalchemy_load_only(*load_only))
#             else:
#                 stmt = select(self.model)
#
#             conditions = self._build_filters(filters, **kwargs)
#             if conditions:
#                 stmt = stmt.where(and_(*conditions))
#
#             if where_clause is not None:
#                 stmt = stmt.where(where_clause)
#
#             result = await db.execute(stmt)
#             return result.first() if columns else result.scalars().first()
#
#         return await self._execute_read_operation(db, "get", _op)
#
#     async def get_multi(
#             self,
#             db: AsyncSession,
#             *,
#             skip: int = 0,
#             limit: int = 100,
#             filters: Optional[Dict[str, Any]] = None,
#             order_by: Optional[Any] = None,
#             load_only: Optional[List[str]] = None,
#             where_clause: Optional[Any] = None,
#             **kwargs: Any
#     ) -> Sequence[ModelType]:
#         """Get multiple records with pagination"""
#
#         async def _op():
#             stmt = select(self.model)
#
#             if load_only:
#                 stmt = stmt.options(sqlalchemy_load_only(*load_only))
#
#             # Use the new _build_filters method
#             conditions = self._build_filters(filters, **kwargs)
#             if conditions:
#                 stmt = stmt.where(and_(*conditions))
#
#             if where_clause is not None:
#                 stmt = stmt.where(where_clause)
#
#             if order_by is not None:
#                 if isinstance(order_by, (list, tuple)):
#                     stmt = stmt.order_by(*order_by)
#                 else:
#                     stmt = stmt.order_by(order_by)
#
#             stmt = stmt.offset(skip).limit(limit)
#             result = await db.execute(stmt)
#             return result.scalars().all()
#
#         return await self._execute_read_operation(db, "get_multi", _op)
#
#     # UPDATE Operations
#     async def update(
#             self,
#             db: AsyncSession,
#             *,
#             db_obj: Optional[ModelType] = None,
#             obj_id: Optional[Any] = None,
#             **kwargs: Any
#     ) -> ModelType:
#         """Update a record"""
#
#         async def _op():
#             nonlocal db_obj
#             if db_obj is None and obj_id is not None:
#                 db_obj = await self.get(db, obj_id=obj_id)
#                 if not db_obj:
#                     raise ValueError(f"Record with id {obj_id} not found")
#             elif db_obj is None:
#                 raise ValueError("Either db_obj or obj_id must be provided")
#
#             for key, value in kwargs.items():
#                 setattr(db_obj, key, value)
#
#             await db.flush()
#             await db.refresh(db_obj)
#             return db_obj
#
#         return await self._execute_write_operation(db, "update", _op)
#
#     async def bulk_update(
#             self,
#             db: AsyncSession,
#             *,
#             filters: Optional[Dict[str, Any]] = None,
#             update_values: Dict[str, Any],
#             where_clause: Optional[Any] = None,
#             **kwargs: Any
#     ) -> int:
#         """Bulk update records"""
#
#         async def _op():
#             stmt = update(self.model)
#
#             conditions = self._build_filters(filters, **kwargs)
#             if conditions:
#                 stmt = stmt.where(and_(*conditions))
#
#             if where_clause is not None:
#                 stmt = stmt.where(where_clause)
#
#             stmt = stmt.values(**update_values)
#
#             result = await db.execute(stmt)
#             return result.rowcount
#
#         return await self._execute_write_operation(db, "bulk_update", _op)
#
#     # DELETE Operations
#     async def delete(
#             self,
#             db: AsyncSession,
#             *,
#             db_obj: Optional[ModelType] = None,
#             obj_id: Optional[Any] = None,
#             filters: Optional[Dict[str, Any]] = None,
#             where_clause: Optional[Any] = None,
#             soft_delete: bool = False,
#             **kwargs: Any
#     ) -> None:
#         """Delete records matching the criteria"""
#         if not any([db_obj, obj_id, filters, where_clause, kwargs]):
#             raise ValueError("Must provide at least one deletion criteria")
#
#         async def _op():
#             nonlocal db_obj
#             if db_obj is not None:
#                 if soft_delete and hasattr(db_obj, 'is_deleted'):
#                     db_obj.is_deleted = True
#                 else:
#                     await db.delete(db_obj)
#             elif obj_id is not None:
#                 db_obj = await self.get(db, obj_id=obj_id)
#                 if not db_obj:
#                     raise ValueError(f"Record with id {obj_id} not found")
#                 if soft_delete and hasattr(db_obj, 'is_deleted'):
#                     db_obj.is_deleted = True
#                 else:
#                     await db.delete(db_obj)
#             else:
#                 if soft_delete and hasattr(self.model, 'is_deleted'):
#                     stmt = update(self.model).values(is_deleted=True)
#                 else:
#                     stmt = delete(self.model)
#
#                 conditions = self._build_filters(filters, **kwargs)
#                 if conditions:
#                     stmt = stmt.where(and_(*conditions))
#
#                 if where_clause is not None:
#                     stmt = stmt.where(where_clause)
#
#                 await db.execute(stmt)
#
#         await self._execute_write_operation(db, "delete", _op)
#
#     # UTILITY Operations
#     async def count(
#             self,
#             db: AsyncSession,
#             *,
#             filters: Optional[Dict[str, Any]] = None,
#             where_clause: Optional[Any] = None,
#             **kwargs: Any
#     ) -> int:
#         """Count records matching filters"""
#
#         async def _op():
#             stmt = select(func.count()).select_from(self.model)
#
#             conditions = self._build_filters(filters, **kwargs)
#             if conditions:
#                 stmt = stmt.where(and_(*conditions))
#
#             if where_clause is not None:
#                 stmt = stmt.where(where_clause)
#
#             result = await db.execute(stmt)
#             return result.scalar_one()
#
#         return await self._execute_read_operation(db, "count", _op)
#
#     async def exists(
#             self,
#             db: AsyncSession,
#             *,
#             filters: Optional[Dict[str, Any]] = None,
#             where_clause: Optional[Any] = None,
#             **kwargs: Any
#     ) -> bool:
#         """Check if records exist matching filters"""
#
#         async def _op():
#             stmt = select(1)
#
#             conditions = self._build_filters(filters, **kwargs)
#             if conditions:
#                 stmt = stmt.where(and_(*conditions))
#
#             if where_clause is not None:
#                 stmt = stmt.where(where_clause)
#
#             result = await db.execute(stmt.limit(1))
#             return result.scalar() is not None
#
#         return await self._execute_read_operation(db, "exists", _op)
#
#     async def paginate(
#             self,
#             db: AsyncSession,
#             *,
#             page: int = 1,
#             per_page: int = 20,
#             filters: Optional[Dict[str, Any]] = None,
#             order_by: Optional[Any] = None,
#             **kwargs: Any
#     ) -> Dict[str, Any]:
#         """Paginated results with metadata"""
#
#         async def _op():
#             skip = (page - 1) * per_page
#
#             total = await self.count(db, filters=filters, **kwargs)
#             items = await self.get_multi(
#                 db,
#                 skip=skip,
#                 limit=per_page,
#                 filters=filters,
#                 order_by=order_by,
#                 **kwargs
#             )
#
#             return {
#                 "items": items,
#                 "total": total,
#                 "page": page,
#                 "per_page": per_page,
#                 "total_pages": (total + per_page - 1) // per_page,
#                 "has_next": page * per_page < total,
#                 "has_prev": page > 1
#             }
#
#         return await self._execute_read_operation(db, "paginate", _op)

# from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy import select, and_, func, update, delete
# from sqlalchemy.exc import IntegrityError, SQLAlchemyError
# from typing import (
#     Generic,
#     TypeVar,
#     Optional,
#     Type,
#     Any,
#     Sequence,
#     List,
#     Dict,
#     Union,
#     Tuple,
# )
# import logging
# from sqlalchemy.orm import load_only as sqlalchemy_load_only
#
# ModelType = TypeVar('ModelType')
# logger = logging.getLogger(__name__)
#
#
# class CrudBase(Generic[ModelType]):
#     def __init__(self, model: Type[ModelType]):
#         """
#         Initialize CRUD operations for a specific model.
#
#         Args:
#             model: SQLAlchemy model class
#         """
#         self.model = model
#
#     @staticmethod
#     async def _execute_write_operation(db: AsyncSession, operation_name: str, db_operation):
#         """
#         Execute a database write operation with error handling and commit.
#         """
#         try:
#             result = await db_operation()
#             await db.commit()
#             return result
#         except IntegrityError as e:
#             await db.rollback()
#             logger.error(f"Integrity error during {operation_name}: {e}")
#             raise
#         except SQLAlchemyError as e:
#             await db.rollback()
#             logger.error(f"Database error during {operation_name}: {e}")
#             raise
#         except Exception as e:
#             await db.rollback()
#             logger.error(f"Unexpected error during {operation_name}: {e}")
#             raise
#
#     @staticmethod
#     async def _execute_read_operation(db: AsyncSession, operation_name: str, db_operation):
#         """
#         Execute a database read operation with error handling.
#         """
#         try:
#             return await db_operation()
#         except SQLAlchemyError as e:
#             logger.error(f"Database error during {operation_name}: {e}")
#             raise
#         except Exception as e:
#             logger.error(f"Unexpected error during {operation_name}: {e}")
#             raise
#
#     # CREATE Operations
#     async def create(self, db: AsyncSession, **kwargs: Any) -> ModelType:
#         """Create a new record"""
#
#         async def _op():
#             db_obj = self.model(**kwargs)
#             db.add(db_obj)
#             await db.flush()
#             await db.refresh(db_obj)
#             return db_obj
#
#         return await self._execute_write_operation(db, "create", _op)
#
#     async def bulk_create(self, db: AsyncSession, objects: List[Dict[str, Any]]) -> List[ModelType]:
#         """Bulk create records"""
#
#         async def _op():
#             db_objects = [self.model(**obj) for obj in objects]
#             db.add_all(db_objects)
#             await db.flush()
#             return db_objects
#
#         return await self._execute_write_operation(db, "bulk_create", _op)
#
#     # READ Operations
#     async def get(
#             self,
#             db: AsyncSession,
#             *,
#             obj_id: Optional[Any] = None,
#             filters: Optional[Dict[str, Any]] = None,
#             columns: Optional[List[str]] = None,
#             load_only: Optional[List[str]] = None,
#             where_clause: Optional[Any] = None,
#             **kwargs: Any
#     ) -> Union[Optional[ModelType], Optional[Tuple]]:
#         """Get a single record with flexible column selection"""
#
#         async def _op():
#             if obj_id is not None:
#                 kwargs['id'] = obj_id
#
#             if columns:
#                 selected = [getattr(self.model, col) for col in columns]
#                 stmt = select(*selected)
#             elif load_only:
#                 stmt = select(self.model).options(sqlalchemy_load_only(*load_only))
#             else:
#                 stmt = select(self.model)
#
#             if filters or kwargs:
#                 conditions = []
#                 for field, value in {**(filters or {}), **kwargs}.items():
#                     column = getattr(self.model, field)
#                     if isinstance(value, (list, tuple)):
#                         conditions.append(column.in_(value))
#                     else:
#                         conditions.append(column == value)
#                 stmt = stmt.where(and_(*conditions))
#
#             if where_clause is not None:
#                 stmt = stmt.where(where_clause)
#
#             result = await db.execute(stmt)
#             return result.first() if columns else result.scalars().first()
#
#         return await self._execute_read_operation(db, "get", _op)
#
#     async def get_multi(
#             self,
#             db: AsyncSession,
#             *,
#             skip: int = 0,
#             limit: int = 100,
#             filters: Optional[Dict[str, Any]] = None,
#             order_by: Optional[Any] = None,
#             load_only: Optional[List[str]] = None,
#             where_clause: Optional[Any] = None,
#             **kwargs: Any
#     ) -> Sequence[ModelType]:
#         """Get multiple records with pagination"""
#
#         async def _op():
#             stmt = select(self.model)
#
#             if load_only:
#                 stmt = stmt.options(sqlalchemy_load_only(*load_only))
#
#             if filters or kwargs:
#                 conditions = []
#                 for field, value in {**(filters or {}), **kwargs}.items():
#                     column = getattr(self.model, field)
#                     if isinstance(value, (list, tuple)):
#                         conditions.append(column.in_(value))
#                     else:
#                         conditions.append(column == value)
#                 stmt = stmt.where(and_(*conditions))
#
#             if where_clause is not None:
#                 stmt = stmt.where(where_clause)
#
#             if order_by is not None:
#                 if isinstance(order_by, (list, tuple)):
#                     stmt = stmt.order_by(*order_by)
#                 else:
#                     stmt = stmt.order_by(order_by)
#
#             stmt = stmt.offset(skip).limit(limit)
#             result = await db.execute(stmt)
#             return result.scalars().all()
#
#         return await self._execute_read_operation(db, "get_multi", _op)
#
#     # UPDATE Operations
#     async def update(
#             self,
#             db: AsyncSession,
#             *,
#             db_obj: Optional[ModelType] = None,
#             obj_id: Optional[Any] = None,
#             **kwargs: Any
#     ) -> ModelType:
#         """Update a record"""
#
#         async def _op():
#             nonlocal db_obj
#             if db_obj is None and obj_id is not None:
#                 db_obj = await self.get(db, obj_id=obj_id)
#                 if not db_obj:
#                     raise ValueError(f"Record with id {obj_id} not found")
#             elif db_obj is None:
#                 raise ValueError("Either db_obj or obj_id must be provided")
#
#             for key, value in kwargs.items():
#                 setattr(db_obj, key, value)
#
#             await db.flush()
#             await db.refresh(db_obj)
#             return db_obj
#
#         return await self._execute_write_operation(db, "update", _op)
#
#     async def bulk_update(
#             self,
#             db: AsyncSession,
#             *,
#             filters: Optional[Dict[str, Any]] = None,
#             update_values: Dict[str, Any],
#             where_clause: Optional[Any] = None,
#             **kwargs: Any
#     ) -> int:
#         """Bulk update records"""
#
#         async def _op():
#             stmt = update(self.model)
#
#             if filters or kwargs:
#                 conditions = []
#                 for field, value in {**(filters or {}), **kwargs}.items():
#                     column = getattr(self.model, field)
#                     conditions.append(column == value)
#                 stmt = stmt.where(and_(*conditions))
#
#             if where_clause is not None:
#                 stmt = stmt.where(where_clause)
#
#             stmt = stmt.values(**update_values)
#
#             result = await db.execute(stmt)
#             return result.rowcount
#
#         return await self._execute_write_operation(db, "bulk_update", _op)
#
#     # DELETE Operations
#     async def delete(
#             self,
#             db: AsyncSession,
#             *,
#             db_obj: Optional[ModelType] = None,
#             obj_id: Optional[Any] = None,
#             filters: Optional[Dict[str, Any]] = None,
#             where_clause: Optional[Any] = None,
#             soft_delete: bool = False,
#             **kwargs: Any
#     ) -> None:
#         """Delete records matching the criteria"""
#         if not any([db_obj, obj_id, filters, where_clause, kwargs]):
#             raise ValueError("Must provide at least one deletion criteria")
#
#         async def _op():
#             nonlocal db_obj
#             if db_obj is not None:
#                 if soft_delete and hasattr(db_obj, 'is_deleted'):
#                     db_obj.is_deleted = True
#                 else:
#                     await db.delete(db_obj)
#             elif obj_id is not None:
#                 db_obj = await self.get(db, obj_id=obj_id)
#                 if not db_obj:
#                     raise ValueError(f"Record with id {obj_id} not found")
#                 if soft_delete and hasattr(db_obj, 'is_deleted'):
#                     db_obj.is_deleted = True
#                 else:
#                     await db.delete(db_obj)
#             else:
#                 if soft_delete and hasattr(self.model, 'is_deleted'):
#                     stmt = update(self.model).values(is_deleted=True)
#                 else:
#                     stmt = delete(self.model)
#
#                 if filters or kwargs:
#                     conditions = []
#                     for field, value in {**(filters or {}), **kwargs}.items():
#                         column = getattr(self.model, field)
#                         conditions.append(column == value)
#                     stmt = stmt.where(and_(*conditions))
#
#                 if where_clause is not None:
#                     stmt = stmt.where(where_clause)
#
#                 await db.execute(stmt)
#
#         await self._execute_write_operation(db, "delete", _op)
#
#     # UTILITY Operations
#     async def count(
#             self,
#             db: AsyncSession,
#             *,
#             filters: Optional[Dict[str, Any]] = None,
#             where_clause: Optional[Any] = None,
#             **kwargs: Any
#     ) -> int:
#         """Count records matching filters"""
#
#         async def _op():
#             stmt = select(func.count()).select_from(self.model)
#
#             if filters or kwargs:
#                 conditions = []
#                 for field, value in {**(filters or {}), **kwargs}.items():
#                     column = getattr(self.model, field)
#                     conditions.append(column == value)
#                 stmt = stmt.where(and_(*conditions))
#
#             if where_clause is not None:
#                 stmt = stmt.where(where_clause)
#
#             result = await db.execute(stmt)
#             return result.scalar_one()
#
#         return await self._execute_read_operation(db, "count", _op)
#
#     async def exists(
#             self,
#             db: AsyncSession,
#             *,
#             filters: Optional[Dict[str, Any]] = None,
#             where_clause: Optional[Any] = None,
#             **kwargs: Any
#     ) -> bool:
#         """Check if records exist matching filters"""
#
#         async def _op():
#             stmt = select(1)
#
#             if filters or kwargs:
#                 conditions = []
#                 for field, value in {**(filters or {}), **kwargs}.items():
#                     column = getattr(self.model, field)
#                     conditions.append(column == value)
#                 stmt = stmt.where(and_(*conditions))
#
#             if where_clause is not None:
#                 stmt = stmt.where(where_clause)
#
#             result = await db.execute(stmt.limit(1))
#             return result.scalar() is not None
#
#         return await self._execute_read_operation(db, "exists", _op)
#
#     async def paginate(
#             self,
#             db: AsyncSession,
#             *,
#             page: int = 1,
#             per_page: int = 20,
#             filters: Optional[Dict[str, Any]] = None,
#             order_by: Optional[Any] = None,
#             **kwargs: Any
#     ) -> Dict[str, Any]:
#         """Paginated results with metadata"""
#
#         async def _op():
#             skip = (page - 1) * per_page
#
#             total = await self.count(db, filters=filters, **kwargs)
#             items = await self.get_multi(
#                 db,
#                 skip=skip,
#                 limit=per_page,
#                 filters=filters,
#                 order_by=order_by,
#                 **kwargs
#             )
#
#             return {
#                 "items": items,
#                 "total": total,
#                 "page": page,
#                 "per_page": per_page,
#                 "total_pages": (total + per_page - 1) // per_page,
#                 "has_next": page * per_page < total,
#                 "has_prev": page > 1
#             }
#
#         return await self._execute_read_operation(db, "paginate", _op)
