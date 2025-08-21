from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.sql import func
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
    price = Column(Float, nullable=False, index=True)
    stock_quantity = Column(Integer, default=0, nullable=False)
    sku = Column(String(100), unique=True, index=True)
    tags = Column(Text)  # JSON string of tags
    status = Column(Enum(ProductStatus), default=ProductStatus.DRAFT, nullable=False)
    weight = Column(Float)  # For delivery calculations
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
    cart_items = relationship("CartItem", back_populates="product")
    order_items = relationship("OrderItem", back_populates="product")
    reviews = relationship("Review", back_populates="product")
    favorites = relationship("Favorite", back_populates="product")


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
