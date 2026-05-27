from typing import List, Optional, TYPE_CHECKING
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import func, ForeignKey, Integer, String, Boolean, DateTime
from tasty.ext.db import db

if TYPE_CHECKING:
    from .user import User
    from .businesshastype import BusinessHasType
    from .businessowner import BusinessOwner
    from .address import Address
    from .businesstype import Businesstype

# ----------------------------------------------------------
# level
# ----------------------------------------------------------

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
    
    # RELACAO N:N REAL
    # Agora uma empresa pode ter uma lista de owners
    owners: Mapped[list["User"]] = relationship(
        "User",
        secondary="business_owners",
        back_populates="owned_businesses"
    )

    # Relacionamento com Endereço (1:1)
    # Cascade garante que se a empresa sumir, o endereço dela também some.
    address: Mapped[Optional["Address"]] = relationship(
        "Address",
        back_populates="business",
        cascade="all, delete-orphan",
        uselist=False
    )

    # N : N FAZER

    business_type: Mapped[List["Businesstype"]] = relationship(
        "BusinessType",
        secondary="businesshastype",
        back_populates="businessesHasType",
    )

    def __repr__(self) -> str:
        return f"<Business {self.trade_name}>"