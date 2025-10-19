from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum
from .base import Base, IntIdMixin, TimeStampMixin


class MerchantApplicationStatus(PyEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUSPENDED = "suspended"


class MerchantApplication(Base, IntIdMixin, TimeStampMixin):
    __tablename__ = "merchant_applications"

    business_name = Column(String(200), nullable=False)
    business_description = Column(Text, nullable=False)
    business_address = Column(Text, nullable=False)
    business_phone = Column(String(20), nullable=False)
    business_email = Column(String(255), nullable=False)
    tax_id = Column(String(50))
    website_url = Column(String(500))
    status = Column(Enum(MerchantApplicationStatus), default=MerchantApplicationStatus.PENDING, nullable=False)
    rejection_reason = Column(Text)
    admin_notes = Column(Text)
    approved_at = Column(DateTime(timezone=True))

    # Foreign Keys
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    approved_by = Column(Integer, ForeignKey("users.id"))

    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="merchant_application")
    approver = relationship("User", foreign_keys=[approved_by])
