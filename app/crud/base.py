from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, select, Row, RowMapping
from typing import Generic, TypeVar, Optional, Type, Any, List, Sequence
from app.utils.responses.exceptions import Exceptions

ModelType = TypeVar("ModelType")


class CrudBase(Generic[ModelType]):
    def __init__(self, model: Type[ModelType]):
        self.model = model

    async def create(self, db: AsyncSession, **kwargs: Any) -> ModelType:
        db_obj = self.model(**kwargs)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get(self, db: AsyncSession, **kwargs) -> Optional[ModelType]:
        return await db.get(self.model, **kwargs)

    async def get_multi(self, db: AsyncSession) -> Sequence[Row | RowMapping | Any]:
        query = select(self.model)
        result = await db.execute(query)
        return result.scalars().all()

    async def get_object_or_404(self, db: AsyncSession, **kwargs) -> ModelType:
        filters = [getattr(self.model, key) == value for key, value in kwargs.items()]
        query = select(self.model).filter(and_(*filters))
        result = await db.execute(query)
        db_obj = result.scalar_one_or_none()

        if not db_obj:
            raise Exceptions.not_found(self.model.__name__)  # Ensure it raises an exception
        return db_obj

    async def update(self, db: AsyncSession, *,
                     db_obj: Optional[ModelType] = None,
                     id: Optional[Any] = None, **kwargs: Any) -> ModelType:
        if db_obj is None:
            db_obj = await self.get_object_or_404(db, id=id)
        for key, value in kwargs.items():
            setattr(db_obj, key, value)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def delete_obj(self, db: AsyncSession, **kwargs) -> ModelType:
        db_obj = await self.get_object_or_404(db, **kwargs)
        await db.delete(db_obj)
        await db.commit()
        return db_obj

    async def delete_multiple(self, db: AsyncSession, ids: List[Any]) -> Sequence[Row | RowMapping | Any]:
        query = select(self.model).filter(self.model.id.in_(ids))
        result = await db.execute(query)
        objects = result.scalars().all()

        if not objects:
            raise Exceptions.no_objects_found()  # Ensure it raises an exception

        for obj in objects:
            await db.delete(obj)
        await db.commit()
        return objects
