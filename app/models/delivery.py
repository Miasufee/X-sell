from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum
from .base import Base, IntIdMixin, TimeStampMixin


class DeliveryStatus(PyEnum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Delivery(Base, IntIdMixin, TimeStampMixin):
    __tablename__ = "deliveries"

    tracking_number = Column(String(100), unique=True, nullable=False, index=True)
    status = Column(Enum(DeliveryStatus), default=DeliveryStatus.PENDING, nullable=False)
    pickup_address = Column(Text, nullable=False)
    delivery_address = Column(Text, nullable=False)
    pickup_latitude = Column(Float, nullable=False)
    pickup_longitude = Column(Float, nullable=False)
    delivery_latitude = Column(Float, nullable=False)
    delivery_longitude = Column(Float, nullable=False)
    distance_km = Column(Float, nullable=False)
    estimated_cost = Column(Float, nullable=False)
    actual_cost = Column(Float)
    weight_kg = Column(Float)
    driver_name = Column(String(200))
    driver_phone = Column(String(20))
    estimated_delivery_time = Column(DateTime(timezone=True))
    actual_delivery_time = Column(DateTime(timezone=True))
    notes = Column(Text)

    # Foreign Keys
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)

    # Relationships
    order = relationship("Order", back_populates="delivery")
