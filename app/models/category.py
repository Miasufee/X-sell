from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base, IntIdMixin, TimeStampMixin


class Category(Base, IntIdMixin, TimeStampMixin):
    __tablename__ = "categories"

    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False)

    # Self-referencing relationship for nested categories
    parent_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    parent = relationship("Category", remote_side="Category.id", backref="children")

    # Relationships
    subcategories = relationship("SubCategory", back_populates="category")
    images = relationship("CategoryImage", back_populates="category", cascade="all, delete-orphan")


class SubCategory(Base, IntIdMixin, TimeStampMixin):
    __tablename__ = "sub_categories"

    name = Column(String(100), nullable=False, index=True)
    description = Column(Text)
    slug = Column(String(100), nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False)

    # Foreign Keys
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)

    # Relationships
    category = relationship("Category", back_populates="subcategories")
    products = relationship("Product", back_populates="subcategory")
    images = relationship("SubCategoryImage", back_populates="subcategory", cascade="all, delete-orphan")


class CategoryImage(Base, IntIdMixin, TimeStampMixin):
    __tablename__ = "category_images"

    image_url = Column(String(255), nullable=False)
    alt_text = Column(String(150), nullable=True)
    is_primary = Column(Boolean, default=False, nullable=False)

    # Foreign Key
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)

    # Relationships
    category = relationship("Category", back_populates="images")


class SubCategoryImage(Base, IntIdMixin, TimeStampMixin):
    __tablename__ = "sub_category_images"

    image_url = Column(String(255), nullable=False)
    alt_text = Column(String(150), nullable=True)
    is_primary = Column(Boolean, default=False, nullable=False)

    # Foreign Key
    subcategory_id = Column(Integer, ForeignKey("sub_categories.id"), nullable=False)

    # Relationships
    subcategory = relationship("SubCategory", back_populates="images")
