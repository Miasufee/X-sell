from sqlalchemy import Column, Integer, String, Text, Float, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base, IntIdMixin, TimeStampMixin


class Shop(Base, IntIdMixin, TimeStampMixin):
    __tablename__ = "shops"

    name = Column(String(200), nullable=False, index=True)
    description = Column(Text)
    address = Column(Text, nullable=False)
    latitude = Column(Float, nullable=False, index=True)
    longitude = Column(Float, nullable=False, index=True)
    phone = Column(String(20))
    email = Column(String(255))
    is_active = Column(Boolean, default=True, nullable=False)


    # Foreign Keys
    merchant_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Relationships
    merchant = relationship("User", back_populates="shops")
    products = relationship("Product", back_populates="shop")
