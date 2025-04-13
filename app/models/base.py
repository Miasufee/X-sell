from sqlalchemy import Column, Integer, DateTime, Boolean, ForeignKey, String, Text
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base, declared_attr

Base = declarative_base()


class IdMixin:
    """
    Mixin to provide a primary key ID column.
    """
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)


class TimeStampMixin:
    """
    Mixin to provide timestamp fields for creation, updates, and soft deletion.
    """
    @declared_attr
    def created_at(cls):
        return Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    @declared_attr
    def updated_at(cls):
        return Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    @declared_attr
    def is_deleted(cls):
        return Column(Boolean, default=False, nullable=False)

    @declared_attr
    def deleted_at(cls):
        return Column(DateTime(timezone=True), nullable=True)


class CategorySubcategoryItemMixin:

    name = Column(String, index=True)
    slug = Column(String, index=True, unique=True)
    seo_title = Column(String, nullable=True)
    seo_description = Column(Text, nullable=True)
