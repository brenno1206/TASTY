from typing import List, Optional, TYPE_CHECKING
from datetime import datetime
from sqlalchemy import func, Integer, String, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from tasty.ext.db import db

if TYPE_CHECKING:
    from .user import User
    from .address import Address
    from .business_type import BusinessType
    from .photo import Photo
    from .business_swipe import BusinessSwipe

class Business(db.Model):
    """Modelo de Estabelecimento Parceiro, representando os negócios que os usuários podem interagir (dar like, super like, etc.) e que possuem proprietários (users) e tipos (business types)."""
    __tablename__ = "businesses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    corporate_name: Mapped[str] = mapped_column(String(120), nullable=False)
    trade_name: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    cnpj: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    opening_time: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    closing_time: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)

    addresses: Mapped[List["Address"]] = relationship(
        "Address", back_populates="business", cascade="all, delete-orphan"
    )
    photos: Mapped[List["Photo"]] = relationship(
        "Photo", back_populates="business", cascade="all, delete-orphan"
    )
    swipes: Mapped[List["BusinessSwipe"]] = relationship(
        "BusinessSwipe", back_populates="business", cascade="all, delete-orphan"
    )

    # N:N Relationships
    owners: Mapped[List["User"]] = relationship(
        "User", secondary="business_owners", back_populates="owned_businesses"
    )
    business_types: Mapped[List["BusinessType"]] = relationship(
        "BusinessType", secondary="business_has_type", back_populates="businesses"
    )

    def __repr__(self) -> str:
        return f"<Business {self.trade_name}>"