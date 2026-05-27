from typing import List, Optional, TYPE_CHECKING
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, Integer, String, Boolean, DateTime, func
from tasty.ext.db import db

if TYPE_CHECKING:
    from .address import Address
    from .role import Role
    from .business import Business
    from .business_type import BusinessType

class User(db.Model):
    __tablename__ = "users"
    __table_args__ = {'extend_existing': True}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)
    phone: Mapped[Optional[str]] = mapped_column(String(45))
    email_verified_at: Mapped[Optional[str]] = mapped_column(String(45))
    photo: Mapped[Optional[str]] = mapped_column(String(255))
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    google_id: Mapped[Optional[str]] = mapped_column(String(100))
    facebook_id: Mapped[Optional[str]] = mapped_column(String(100))
    cpf: Mapped[Optional[str]] = mapped_column(String(20), unique=True)
    created_at: Mapped[Optional[str]] = mapped_column(String(45)) # Pode usar DateTime depois se quiser
    updated_at: Mapped[Optional[str]] = mapped_column(String(45))
    is_active: Mapped[Optional[str]] = mapped_column(String(45), default="True")

    # FK Role
    role_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("roles.id", ondelete="SET NULL"), index=True
    )

    # Relacionamentos
    role: Mapped[Optional["Role"]] = relationship("Role", back_populates="users")
    addresses: Mapped[List["Address"]] = relationship("Address", back_populates="user", cascade="all, delete-orphan")
    
    # N:N
    owned_businesses: Mapped[List["Business"]] = relationship(
        "Business", secondary="business_owners", back_populates="owners"
    )
    preferences: Mapped[List["BusinessType"]] = relationship(
        "BusinessType", secondary="preferences", back_populates="users"
    )

    def __repr__(self) -> str:
        return f"<User {self.name}>"