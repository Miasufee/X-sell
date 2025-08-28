from sqlalchemy import Column, Integer, String, Text, Float, Boolean, ForeignKey, Enum
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum

from .base import Base, IntIdMixin, TimeStampMixin


class ProductStatus(PyEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    INACTIVE = "inactive"
    OUT_OF_STOCK = "out_of_stock"


class Product(Base, IntIdMixin, TimeStampMixin):
    __tablename__ = "products"

    name = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=False)
    tags = Column(Text)  # JSON string of tags
    status = Column(Enum(ProductStatus), default=ProductStatus.DRAFT, nullable=False)
    is_featured = Column(Boolean, default=False)
    view_count = Column(Integer, default=0)

    # Foreign Keys
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=False)
    merchant_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Relationships
    category = relationship("Category", back_populates="products")
    shop = relationship("Shop", back_populates="products")
    merchant = relationship("User", back_populates="products")

    images = relationship("ProductImage", back_populates="product", cascade="all, delete-orphan")
    reviews = relationship("Review", back_populates="product")
    favorites = relationship("Favorite", back_populates="product")

    # New relationships
    variants = relationship("ProductVariant", back_populates="product", cascade="all, delete-orphan")
    attributes = relationship("ProductAttribute", back_populates="product", cascade="all, delete-orphan")


class ProductImage(Base, IntIdMixin, TimeStampMixin):
    __tablename__ = "product_images"

    url = Column(String(500), nullable=False)
    alt_text = Column(String(200))
    is_primary = Column(Boolean, default=False)
    sort_order = Column(Integer, default=0)

    # Foreign Keys
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)

    # Relationships
    product = relationship("Product", back_populates="images")


class ProductAttribute(Base, IntIdMixin, TimeStampMixin):
    __tablename__ = "product_attributes"

    name = Column(String(100), nullable=False, index=True)  # e.g., "Color", "Size"

    # Foreign Key
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)

    # Relationships
    product = relationship("Product", back_populates="attributes")
    values = relationship("ProductAttributeValue", back_populates="attribute", cascade="all, delete-orphan")


class ProductAttributeValue(Base, IntIdMixin, TimeStampMixin):
    __tablename__ = "product_attribute_values"

    value = Column(String(100), nullable=False)  # e.g., "Red", "XL"

    # Foreign Keys
    attribute_id = Column(Integer, ForeignKey("product_attributes.id"), nullable=False)

    # Relationships
    attribute = relationship("ProductAttribute", back_populates="values")
    variant_links = relationship("ProductVariantAttribute", back_populates="attribute_value", cascade="all, delete-orphan")


class ProductVariant(Base, IntIdMixin, TimeStampMixin):
    __tablename__ = "product_variants"

    sku = Column(String(100), unique=True, nullable=False, index=True)
    price = Column(Float, nullable=False)
    stock_quantity = Column(Integer, default=0, nullable=False)
    weight = Column(Float)

    # Foreign Keys
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)

    # Relationships
    product = relationship("Product", back_populates="variants")
    attributes = relationship("ProductVariantAttribute", back_populates="variant", cascade="all, delete-orphan")


class ProductVariantAttribute(Base, IntIdMixin, TimeStampMixin):
    __tablename__ = "product_variant_attributes"

    # Foreign Keys
    variant_id = Column(Integer, ForeignKey("product_variants.id"), nullable=False)
    attribute_value_id = Column(Integer, ForeignKey("product_attribute_values.id"), nullable=False)

    # Relationships
    variant = relationship("ProductVariant", back_populates="attributes")
    attribute_value = relationship("ProductAttributeValue", back_populates="variant_links")
