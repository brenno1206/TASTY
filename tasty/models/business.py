from typing import List, Optional, TYPE_CHECKING
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import func, Integer, String, Boolean, DateTime
from tasty.ext.db import db

if TYPE_CHECKING:
    from .user import User
    from .address import Address
    from .business_type import BusinessType
    from .photo import Photo

class Business(db.Model):
    __tablename__ = "businesses"
    __table_args__ = {'extend_existing': True}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    corporate_name: Mapped[str] = mapped_column(String(120), nullable=False)
    trade_name: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    cnpj: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # Colunas da imagem
    opening_time: Mapped[Optional[str]] = mapped_column(String(45))
    closing_time: Mapped[Optional[str]] = mapped_column(String(45))

    # Relacionamento com Endereço (1:N caso tenha múltiplos no futuro, mas configurado com uselist=False para 1:1 caso deseje)
    addresses: Mapped[List["Address"]] = relationship(
        "Address", back_populates="business", cascade="all, delete-orphan"
    )

    # Relacionamento com Fotos (1:N)
    photos: Mapped[List["Photo"]] = relationship(
        "Photo", back_populates="business", cascade="all, delete-orphan"
    )

    # N:N com Users (Donos)
    owners: Mapped[List["User"]] = relationship(
        "User", secondary="business_owners", back_populates="owned_businesses"
    )

    # N:N com BusinessTypes
    business_types: Mapped[List["BusinessType"]] = relationship(
        "BusinessType", secondary="business_has_type", back_populates="businesses"
    )

    def __repr__(self) -> str:
        return f"<Business {self.trade_name}>"