from typing import List, Optional, TYPE_CHECKING
from datetime import datetime
from sqlalchemy import ForeignKey, Integer, String, Boolean, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from tasty.ext.db import db

if TYPE_CHECKING:
    from .address import Address
    from .role import Role
    from .business import Business
    from .business_type import BusinessType
    from .business_swipe import BusinessSwipe

class User(db.Model):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)
    phone: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    email_verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    photo: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    google_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    facebook_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    cpf: Mapped[Optional[str]] = mapped_column(String(20), unique=True, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)

    # FK Role
    role_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("roles.id", ondelete="SET NULL"), index=True, nullable=True
    )

    # Relacionamentos
    role: Mapped[Optional["Role"]] = relationship("Role", back_populates="users")
    addresses: Mapped[List["Address"]] = relationship("Address", back_populates="user", cascade="all, delete-orphan")
    swipes: Mapped[List["BusinessSwipe"]] = relationship("BusinessSwipe", back_populates="user", cascade="all, delete-orphan")
    
    # N:N العلاقات
    owned_businesses: Mapped[List["Business"]] = relationship(
        "Business", secondary="business_owners", back_populates="owners"
    )
    preferences: Mapped[List["BusinessType"]] = relationship(
        "BusinessType", secondary="preferences", back_populates="users"
    )

    def __repr__(self) -> str:
        return f"<User {self.name}>"